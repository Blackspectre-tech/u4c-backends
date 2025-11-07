from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
import json
from .blockchain import contract, send_owner_tx
from django.views.decorators.csrf import csrf_exempt
from projects.models import Project,Milestone,Donation
from decimal import Decimal
from .models import ContractLog
from accounts.models import Transaction,Wallet
import datetime
import traceback

#Webhook

EVENT_TOPIC_MAP = {
'0x54225ce5de7dc72a6f5cf898ef7283ada08aadfba3372fc87dfd0bf689261e45' : 'CampaignCreated',
# '0xc67423104bf96f5ca8826913ae711e8c2254e1b2c04af907b2312853ed4cbed2' : 'MilestoneAdded',
'0xf36ffe7645287fddf6deab03a17f4f024a0551da54638685d25cac0dbdf5b6be' : 'Pledged',
'0xfcd29b1632c6748a9a4bb9b4cd5c6486c3c84a8550dce2368f83fef3969d9685' : 'Unpledged',
'0x7c387a42b7678e1b26d65927d4a0176444d9c6509a72583dee248753b768db41' : 'CampaignStateChanged',
'0xffe56bf760f6d13072fce783b476e75aa4fec7f9319bd00fd896ad53bd325848' : 'MilestoneApproved',
'0xfdad5626a5dc3ef449341e73d009a9349b676bb5b58cbb8201e7440e77692725' : 'MilestoneWithdrawn',
'0x7ca5472b7ea78c2c0141c5a12ee6d170cf4ce8ed06be3d22c8252ddfc7a6a2c4' : 'Refunded',
'0x73238e3ae0a71b401b31ae67204506d074de41bd5c084082fba9b64b1c7fa28f' : 'PlatformWalletUpdated',
'0x12d0978e09577356906c174508d8758fbe5e9cc762c7d94a64d74817039b937c' : 'FeeUpdated(uint96)',
'0x1da521c13439ac6ab125c52e0da7dd7de929f09e58aa0f89ebe3dbb12e63a52b' : 'TokenAllowlistUpdated',
'0x62e78cea01bee320cd4e420270b5ea74000d11b0c9f74754ebdbfc544b05a258' : 'Paused',
'0x5db9ee0a495bf2e6ff9c91a7834c1ba4fdd244a5e8aa4e537bd38aeae4b073aa' : 'Unpaused',
'0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0' : 'OwnershipTransferred',
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
            ContractLog.objects.create(data=data, error="no log recieved")
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
                #print(event_args)
                # --- Events ---
                if event_name == 'CampaignCreated':
                    try:
                        campaign_id = event_args['id']
                        creator = event_args['creator']
                        goal = Decimal(event_args['goal']) / (Decimal(10) ** 6)
                        # aware_datetime = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        raw_deadline = event_args.get('deadline')
                        # dt_utc = datetime.datetime.fromtimestamp(int(raw_deadline), tz=timezone.utc)
                        dt_utc = datetime.datetime.fromtimestamp(int(raw_deadline), tz=datetime.timezone.utc)
                        project = Project.objects.filter(
                            approval_status=Project.APPROVED,
                            deployed=False,
                            wallet_address__iexact=creator,
                            goal=goal.quantize(Decimal('0.01'))
                        ).first()
                        project.contract_id = campaign_id
                        project.deployed = True
                        project.deadline = dt_utc
                        project.milestones.filter(milestone_no=1).update(status=Milestone.ACTIVE)
                        project.save(update_fields=['contract_id', 'deployed', 'deadline'])
                        wallet = Wallet.objects.get(address__iexact=creator)
                        Transaction.objects.create(
                            tx_hash = logs[0]['transaction'].get('hash'),
                            event = Transaction.C_DEPLOYMENT,
                            status = Transaction.SUCCESSFUL,
                            wallet = wallet,
                        )
                    except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            ) 
                elif event_name == 'Pledged':
                    try:
                        campaign_id = event_args['id']
                        backer = event_args['backer']
                        net_amount = Decimal(event_args['netAmount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                        tipAmount = Decimal(event_args['tipAmount'])/ (Decimal(10) ** 6)
                        tip = Decimal(str(tipAmount)) if tipAmount != 0 else Decimal(0)
                        pledged_project = Project.objects.get(contract_id=campaign_id)
                        transaction = Transaction.objects.filter(
                                wallet__address__iexact = backer,
                                amount=net_amount,
                                tip=tip,
                                project = pledged_project,
                                status=Transaction.PENDING,
                            ).first()
                        
                        if pledged_project:                            
                            active_milestone = pledged_project.milestones.filter(status=Milestone.ACTIVE).first()

                            # Update the project's total funds.
                            pledged_project.total_funds += net_amount
                            pledged_project.progress = round((pledged_project.total_funds / pledged_project.goal)*100, 2)
                            pledged_project.save(update_fields=['total_funds','progress'])
        
                            # Check if there is an active milestone and if the goal is met.
                            if active_milestone and pledged_project.total_funds >= active_milestone.goal:
                                # Mark the current active milestone as completed.
                                active_milestone.status = Milestone.COMPLETED
                                active_milestone.save(update_fields=['status'])

                                # Determine the number of the next milestone.
                                next_milestone_no = active_milestone.milestone_no + 1

                                # Find the next milestone.
                                next_milestone = pledged_project.milestones.filter(milestone_no=next_milestone_no).first()

                                # If the next milestone exists, activate it.
                                if next_milestone:
                                    next_milestone.status = Milestone.ACTIVE
                                    next_milestone.save(update_fields=['status'])
                                # else:
                                #     send_owner_tx(contract.functions.finalize(campaign_id))
                            
                            transaction.status = Transaction.SUCCESSFUL
                            transaction.tx_hash = logs[0]['transaction'].get('hash')
                            transaction.save(update_fields=['status', 'tx_hash'])

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
                                    wallet=transaction.wallet,
                                )
                        else: 
                            ContractLog.objects.create(
                                data=data,
                                error="could not find project",
                                notes=event_args
                            )
                    except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            ) 

                # elif event_name == 'MilestoneAdded':
                #     try:
                #         campaign_id = event_args['id']
                #         milestone_index = event_args['index']
                #         amount = Decimal(event_args['amount']) / (Decimal(10) ** 6)
                #         project = Project.objects.get(contract_id = campaign_id)
                #         milestone = project.milestones.get(goal=amount.quantize(Decimal('0.01')))
                #         milestone.contract_index=milestone_index
                #         milestone.save(update_fields=['contract_index'])
                #     except Exception as e:
                #             #print(f"{e} traceback: {traceback.format_exc()}")
                #             ContractLog.objects.create(
                #                 data=data,
                #                 error=str(e),
                #                 notes=traceback.format_exc()
                #             ) 

                elif event_name == 'CampaignStateChanged':
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
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )  

                elif event_name == 'MilestoneApproved':
                        try :
                            campaign_id = event_args['id']
                            #index = event_args['index']
                            amount = Decimal(event_args['amount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                            project = Project.objects.get(contract_id = campaign_id)
                            milestone = project.milestones.get(goal=amount)
                            milestone.approved= True
                            milestone.save(update_fields=['approved'])
                        except:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )      

                elif event_name == 'MilestoneWithdrawn':
                        try :
                            campaign_id = event_args['id']
                            #index = event_args['index']
                            amount = Decimal(event_args['amount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                            project = Project.objects.get(contract_id = campaign_id)
                            milestone = project.milestones.get(goal=amount)
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
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )    



                elif event_name == 'Refunded':
                        try :
                            campaign_id = event_args['id']
                            backer = event_args['backer']
                            amount = Decimal(event_args['amount']) / (Decimal(10) ** 6).quantize(Decimal('0.01'))
                            project = Project.objects.get(contract_id = campaign_id)
                            donation = project.donations.filter(wallet__address=backer).first().update(refundable=False,refunded=True)
                            Transaction.objects.create(
                                wallet = donation.wallet,
                                tx_hash = logs[0]['transaction'].get('hash'),
                                event = Transaction.REFUND,
                                status = Transaction.SUCCESSFUL,
                            )
                        except Exception as e:
                            #print(f"{e} traceback: {traceback.format_exc()}")
                            ContractLog.objects.create(
                                data=data,
                                error=str(e),
                                notes=traceback.format_exc()
                            )    



            except Exception as e:
                print(f"{e} traceback: {traceback.format_exc()}")
                ContractLog.objects.create(
                    data=data,
                    error=str(e),
                    notes=traceback.format_exc()
                )

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': f'an error occurred: {e} traceback: {traceback.format_exc()}'}, status=500)