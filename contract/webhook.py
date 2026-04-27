from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
import json
from .blockchain import contract, send_owner_tx
from django.views.decorators.csrf import csrf_exempt
from projects.models import Project,Milestone,Donation
from decimal import Decimal
from website.models import ErrorLog
from accounts.models import Transaction,Wallet, Donor
import datetime
import traceback
from django.utils import timezone
from django.db.models import F
from accounts.utils import send_html_mail

#Webhook


EVENT_TOPIC_MAP = {
'0xf6927b61d53c52832973f54bb03898d046415a87f616d486523e1b663315364d' : 'CampaignCreated',
'0x242b7d43c73f615dfdfa4919702ad9db4880a3b095d19100eb73c3d05e92be15' : 'CampaignFinalized',
'0x66db9066eef427bc79cc914343b2a5810df710dd78414eeb82edfd7780941cd6' : 'Pledged',
'0x1b29c0842d854a7d068404ef8054846a234308cb5f9f72281ffe0c5d9901e9df' : 'CampaignHalted',
'0x939da3b627c123c81fe5aacebf925163337a0d4f8a03724640618078cad24894' : 'MilestoneApproved',
'0xacd04361f4b63fc14956006d9cdccbcea11dde8e3f5e13dafb34bb10996d7cbf' : 'MilestoneWithdrawn',
'0xf3f402280ef0a7905e124aa621b65eaeb2725c343e8b36d398ed78c29daf285c' : 'RefundClaimed',

}



def _to_int_maybe_hex(v):
    """Accept int, decimal string, or hex string like '0x1' and return int or None."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            if v.startswith(("0x", "0X")):
                return int(v, 16)
            return int(v)
        except Exception:
            return None
    return None

def _normalize_alchemy_log(raw_log, block_obj=None):
    """
    Convert Alchemy webhook log shape into the geth/web3-style log dict that
    contract.events.X().process_log expects.
    """
    tx = raw_log.get("transaction") or {}
    block = block_obj or {}

    return {
        "address": raw_log.get("account", {}).get("address") or raw_log.get("address"),
        "topics": raw_log.get("topics", []),
        "data": raw_log.get("data", "0x"),
        # numeric fields normalized to ints (web3 expects ints or numeric-like)
        "blockNumber": _to_int_maybe_hex(raw_log.get("blockNumber") or block.get("number")),
        "blockHash": raw_log.get("blockHash") or block.get("hash"),
        "transactionHash": tx.get("hash") or raw_log.get("transactionHash"),
        "transactionIndex": _to_int_maybe_hex(raw_log.get("transactionIndex") or tx.get("index")),
        # Alchemy uses 'index' for log index; web3 expects 'logIndex'
        "logIndex": _to_int_maybe_hex(raw_log.get("logIndex") or raw_log.get("index")),
        "removed": raw_log.get("removed", False),
    }

@csrf_exempt
def alchemy_webhook(request):
    """
    Receives and processes Alchemy webhook events for the MilestoneCrowdfund contract.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid method'}, status=405)

    try:
        # Note: Implement HMAC signature verification for production.
        data = json.loads(request.body)
        # logs = data.get('event', {}).get('data', {}).get('block', {}).get('logs', [])
        logs = data['event']['data']['block'].get('logs',[])

        if not logs:
            ErrorLog.objects.create(data=data, error="no log recieved")
            return JsonResponse({'status': 'no logs received'})

        # capture block object for normalization (if present)
        block_obj = data.get('event', {}).get('data', {}).get('block', {})

        for raw_log in logs:
            # normalize Alchemy log into web3/geth style
            web3_log = _normalize_alchemy_log(raw_log, block_obj=block_obj)

            # get topic safely (may be missing)
            topics = web3_log.get("topics") or []
            if not topics:
                #ContractLog.objects.create(data=data, error="no topics in log",notes=raw_log)
                continue

            event_topic = topics[0]

            try:
                # Use the event topic to get the event object from the contract ABI.
                event_name = EVENT_TOPIC_MAP.get(event_topic, None)
                if not event_name:
                    # ContractLog.objects.create(data=data, error="⚠️ Unknown event topic received",notes=raw_log)
                    continue

                # Access the event object directly via the contract instance
                event_object = getattr(contract.events, event_name)

                # PASS THE NORMALIZED web3_log TO process_log
                event_data = event_object().process_log(web3_log)
                event_args = event_data['args']
                print(event_args)
                # --- Events ---
                if event_name == 'CampaignCreated':
                    try:
                        campaign_id = event_args['id']
                        offchain_id = event_args['offchainId']
                        creator = event_args['creator']
                        # goal = Decimal(event_args['goal']) / (Decimal(10) ** 6)
                        # aware_datetime = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        raw_deadline = event_args.get('deadline')
                        # dt_utc = datetime.datetime.fromtimestamp(int(raw_deadline), tz=timezone.utc)
                        dt_utc = datetime.datetime.fromtimestamp(int(raw_deadline), tz=datetime.timezone.utc)
                        # project = Project.objects.filter(
                        #     approval_status=Project.APPROVED,
                        #     deployed=False,
                        #     wallet_address__iexact=creator,
                        #     goal=goal.quantize(Decimal('0.01'))
                        # ).first()
                        project = Project.objects.filter(
                            id = offchain_id 
                        ).first()
                        project.contract_id = campaign_id
                        project.deployed = True
                        project.deadline = dt_utc
                        project.deployed_at = timezone.now()
                        project.wallet_address = creator
                        project.milestones.filter(milestone_no=1).update(status=Milestone.ACTIVE)
                        project.save(update_fields=['contract_id', 'deployed', 'deadline','deployed_at', 'wallet_address'])
                        wallet = Wallet.objects.get(address__iexact=creator)
                        Transaction.objects.create(
                            tx_hash = logs[0]['transaction'].get('hash'),
                            event = Transaction.C_DEPLOYMENT,
                            status = Transaction.SUCCESSFUL,
                            wallet = wallet,
                        )
                    except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            ) 
                elif event_name == 'Pledged':
                    try:
                        campaign_id = event_args['id']
                        backer = event_args['donor']
                        net_amount = Decimal(event_args['netAmount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                        # fee_amount = Decimal(event_args['feeAmount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))                        
                        tipAmount = Decimal(event_args['tipAmount'])/ (Decimal(10) ** 6)
                        tip = Decimal(str(tipAmount)) if tipAmount != 0 else Decimal(0)
                        pledged_project = Project.objects.get(contract_id=campaign_id)
                        

                        if pledged_project:
                            # 1. Update project funds atomically
                            pledged_project.total_funds = F('total_funds') + net_amount
                            pledged_project.save(update_fields=['total_funds'])
                            pledged_project.refresh_from_db()

                            # 2. Update progress
                            pledged_project.progress = round((pledged_project.total_funds / pledged_project.goal) * 100, 2)
                            pledged_project.save(update_fields=['progress'])

                            # 3. Recursive Milestone Ripple
                            # We use a loop because one donation might clear multiple milestones
                            while True:
                                active_milestone = pledged_project.milestones.filter(status=Milestone.ACTIVE).first()
                                
                                # Fallback: If no milestone is active, find the first pending one to start the chain
                                if not active_milestone:
                                    active_milestone = pledged_project.milestones.filter(status=Milestone.NOT_STARTED).order_by('milestone_no').first()
                                    if active_milestone:
                                        active_milestone.status = Milestone.ACTIVE
                                        active_milestone.save(update_fields=['status'])
                                    else:
                                        # No more milestones exist at all
                                        break

                                # Check if the CURRENT active milestone's cumulative goal is met
                                if pledged_project.total_funds >= active_milestone.goal:
                                    active_milestone.status = Milestone.COMPLETED
                                    active_milestone.save(update_fields=['status'])



                                    email = pledged_project.organization.user.email
                                    subject=f"A Milestone Has Been Achieved"
                                    message=f"""Milestone {active_milestone.milestone_no} of your campaign “{pledged_project.title}” has been  successfully completed and verified.
                                                You can view the update on your dashboard.
                                            """
                                    send_html_mail(email,subject,message)


                                    # Look for the next one
                                    next_milestone = pledged_project.milestones.filter(
                                        milestone_no=active_milestone.milestone_no + 1
                                    ).first()

                                    if next_milestone:
                                        next_milestone.status = Milestone.ACTIVE
                                        next_milestone.save(update_fields=['status'])
                                        # Continue the loop to see if the NEW active milestone is also met
                                        continue 
                                    else:
                                        # Goal met and no more milestones to activate
                                        break
                                else:
                                    # Current milestone goal not yet met, stop rippling
                                    break

                                
                            wallet = Wallet.objects.filter(address=backer).first()
                            if wallet:
                                Transaction.objects.create(
                                    project = pledged_project,
                                    wallet = wallet,
                                    amount=net_amount,
                                    tip=tip,
                                    status=Transaction.SUCCESSFUL,
                                    tx_hash = logs[0]['transaction'].get('hash'),
                                    event = Transaction.PLEDGE,
                                    )
                                
                                donor_id = wallet.users.filter(is_organization=False).first().donor.id
                                Donor.objects.filter(id=donor_id).update(tx_count=F('tx_count') + 1)


                                # transaction.status = Transaction.SUCCESSFUL
                                # transaction.tx_hash = logs[0]['transaction'].get('hash')
                                # transaction.save(update_fields=['status', 'tx_hash'])

                            user_donations = Donation.objects.filter(
                                wallet__address__iexact=backer, 
                                project = pledged_project
                                ).first()
                            
                            if user_donations:
                                user_donations.amount = user_donations.amount + net_amount
                                user_donations.save(update_fields=['amount'])
                            else:
                                Donation.objects.create(
                                    project=pledged_project,
                                    amount=net_amount,
                                    wallet=wallet,
                                )
                            
                            email = wallet.users.first().email
                            subject=f"Your Donation Was Successful"
                            message=f"""
                            Your donation of {net_amount} USDC to the campaign “{pledged_project.title}” has been successfully processed. 
                            Thank you for your contribution"""
                            send_html_mail(email,subject,message)


                        else: 
                            ErrorLog.objects.create(
                                data=data,
                                error="could not find project",
                                notes=event_args
                            )
                    except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            ) 


                elif event_name == 'CampaignFinalized':
                        try:
                            campaign_id = event_args['id']
                            state = event_args['newState']
                            #print(f'id:{campaign_id} type:{type(campaign_id)}')
                            project = Project.objects.get(contract_id = campaign_id)
                            if state == 1:
                                project.status = Project.Completed
                            elif state == 2:
                                project.status = Project.Failed
                                project.donations.update(refundable=True)
                            project.save(update_fields=['status'])
                
                        except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )  
                

                elif event_name == 'CampaignHalted':
                        try:
                            campaign_id = event_args['id']
                            project = Project.objects.get(contract_id = campaign_id)
                            project.status = Project.Cancelled
                            project.donations.update(refundable=True)
                            project.save(update_fields=['status'])
                
                        except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )  


                elif event_name == 'MilestoneApproved':
                        try :
                            campaign_id = event_args['id']
                            #index = event_args['index']
                            milestone_index = event_args['milestoneIndex'] + 1
                            project = Project.objects.get(contract_id = campaign_id)
                            milestone = project.milestones.get(milestone_no=milestone_index)
                            milestone.approved= True
                            milestone.save(update_fields=['approved'])

                            email = project.organization.user.email
                            subject=f"Milestone Approved"
                            title = "Progress Verified"
                            message=f"""Milestone {milestone_index} for your campaign '{project.title}'  has been successfully reviewed and approved.
                                        Funds tied to this stage have now been released.You can continue tracking updates and upcoming milestones on your dashboard.
                                    """
                            send_html_mail(email,subject,message,title)

                        except:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )      

                elif event_name == 'MilestoneWithdrawn':
                        try :
                            campaign_id = event_args['id']
                            index = event_args['milestoneIndex'] + 1
                            # amount = Decimal(event_args['amount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                            project = Project.objects.get(contract_id = campaign_id)
                            milestone = project.milestones.get(milestone_no=index)
                            milestone.withdrawn= True
                            milestone.save(update_fields=['withdrawn'])
                            wallet = Wallet.objects.get(address__iexact=logs[0]['transaction']['from'].get('address'))
                            Transaction.objects.create(
                                wallet=wallet,
                                tx_hash = logs[0]['transaction'].get('hash'),
                                event = Transaction.M_WITHDRAWAL,
                                status = Transaction.SUCCESSFUL,
                            )
                        except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )    



                elif event_name == 'Refunded':
                        try :
                            campaign_id = event_args['id']
                            backer = event_args['donor']
                            # amount = Decimal(event_args['amount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                            project = Project.objects.get(contract_id = campaign_id)
                            donation = project.donations.filter(wallet__address=backer)
                            donation.update(refundable=False,refunded=True)
                            donation_obj = donation.first()
                            Transaction.objects.create(
                                wallet = donation_obj.wallet,
                                tx_hash = logs[0]['transaction'].get('hash'),
                                event = Transaction.REFUND,
                                status = Transaction.SUCCESSFUL,
                            )
                        except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ErrorLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )    



            except Exception as e:
                #print(f"{e} traceback: {traceback.format_exc()}")
                ErrorLog.objects.create(
                    data=data,
                    error=str(e),
                    notes=traceback.format_exc()
                )

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': f'an error occurred: {e} traceback: {traceback.format_exc()}'}, status=500)