from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import json
from .blockchain import contract, send_owner_tx
from django.views.decorators.csrf import csrf_exempt
from projects.models import Project,Milestone,Donation
from accounts.models import User
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction



def approve_milestone(campaign_id: int, index: int):
    return send_owner_tx(contract.functions.approveMilestone(campaign_id, index))

def withdraw_milestone(campaign_id: int, index: int):
    return send_owner_tx(contract.functions.withdrawMilestone(campaign_id, index))


def finalize_campaign(campaign_id: int):
    return send_owner_tx(contract.functions.finalize(campaign_id))





@staff_member_required
@require_POST
def set_platform_wallet(request):
    try:
        data = json.loads(request.body)
        wallet = data.get('wallet_address')
        if not wallet:
            return JsonResponse({'ok': False, 'error': 'wallet_address required'}, status=400)

        # CALL YOUR FUNCTION HERE (synchronous example)
        # tx_hash = set_platform_wallet(wallet)
        tx_hash = send_owner_tx(contract.functions.setPlatformWallet(wallet))

        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@staff_member_required
@require_POST
def set_allowed_token(request):
    try:
        data = json.loads(request.body)
        token = data.get('token_address')
        allowed = data.get('allowed')
        if token is None or allowed is None:
            return JsonResponse({'ok': False, 'error': 'token_address and allowed required'}, status=400)
        # convert allowed string to boolean
        if isinstance(allowed, str):
            allowed_bool = allowed.lower() in ('true','1','yes')
        else:
            allowed_bool = bool(allowed)

        # tx_hash = set_allowed_token(token, allowed_bool)
        tx_hash = send_owner_tx(contract.functions.setTokenAllowed(token, allowed_bool))
        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@staff_member_required
@require_POST
def transfer_ownership(request):
    try:
        data = json.loads(request.body)
        new_owner = data.get('new_owner')
        if not new_owner:
            return JsonResponse({'ok': False, 'error': 'new_owner required'}, status=400)
        # tx_hash = transfer_ownership(new_owner)
        tx_hash = send_owner_tx(contract.functions.transferOwnership(new_owner))
        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@staff_member_required
@require_POST
def pause(request):
    try:
        # tx_hash = pause_contract()
        tx_hash = send_owner_tx(contract.functions.pause())
        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@staff_member_required
@require_POST
def unpause(request):
    try:
        # tx_hash = unpause_contract()
        tx_hash = send_owner_tx(contract.functions.unpause())
        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@staff_member_required
@require_POST
def set_fee_bps(request):
    try:
        data = json.loads(request.body)
        fee_bps = data.get('fee_bps')
        if fee_bps is None:
            return JsonResponse({'ok': False, 'error': 'fee_bps required'}, status=400)
        # cast to int
        fee_bps = int(fee_bps)
        # tx_hash = set_fee_bps(fee_bps)
        tx_hash = send_owner_tx(contract.functions.setFeeBps(fee_bps))
        return JsonResponse({'ok': True, 'tx_hash': tx_hash})
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'fee_bps must be integer'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


#Webhook

# Map topic hashes to event names for easy lookup
# Replace the placeholder hashes with the actual hashes you calculated
EVENT_TOPIC_MAP = {
    "0x54225ce5de7dc72a6f5cf898ef7283ada08aadfba3372fc87dfd0bf689261e45": "CampaignCreated",
    "0xa004e6fb17cfc09684ed6477bd1bb07ff609d881603cda693bca2a233d507d94": "Pledged",
    "0xfcd29b1632c6748a9a4bb9b4cd5c6486c3c84a8550dce2368f83fef3969d9685": "Unpledged",
    "0x7c387a42b7678e1b26d65927d4a0176444d9c6509a72583dee248753b768db41": "CampaignStateChanged",
    "0xffe56bf760f6d13072fce783b476e75aa4fec7f9319bd00fd896ad53bd325848": "MilestoneApproved",
    "0xfdad5626a5dc3ef449341e73d009a9349b676bb5b58cbb8201e7440e77692725": "MilestoneWithdrawn",
    "0x7ca5472b7ea78c2c0141c5a12ee6d170cf4ce8ed06be3d22c8252ddfc7a6a2c4": "Refunded",
    "0xc67423104bf96f5ca8826913ae711e8c2254e1b2c04af907b2312853ed4cbed2": "MilestoneAdded",
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
        logs = data.get('logs', []) or data.get('event', {}).get('logs', [])

        if not logs:
            return JsonResponse({'status': 'no logs received'})

        for log in logs:
            event_topic = log['topics'][0]

            try:
                # Use the event topic to get the event object from the contract ABI.
                event_name = EVENT_TOPIC_MAP.get(event_topic, None)
                if not event_name:
                    print(f"⚠️ Unknown event topic received: {event_topic}")
                    continue

                # Access the event object directly via the contract instance
                event_object = getattr(contract.events, event_name)
                event_data = event_object().process_log(log)
                event_args = event_data['args']

                print(f"✅ Received {event_name} event.")
                print(f"Arguments: {event_args}")

                # --- Your Business Logic Starts Here ---
                if event_name == 'CampaignCreated':
                    campaign_id = event_args['id']
                    creator = event_args['creator']
                    goal = Decimal(event_args['goal']) /(Decimal(10)**6)
                    #aware_datetime = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    project = Project.objects.get(
                    approval_status=Project.APPROVED,
                    deployed=False,
                    wallet_address=creator,
                    goal=goal
                    )
                    project.contract_id = campaign_id
                    project.deployed = True
                    project.milestones.filter(milestone_no=1).update(status=Milestone.ACTIVE)
                    project.save(update_fields=['contract_id','deployed'])


                elif event_name == 'Pledged':
                    campaign_id = event_args['id']
                    backer = event_args['backer']
                    net_amount = Decimal(event_args['netAmount']) /(Decimal(10)**6)
                    tip = Decimal(event_args['tip']) /(Decimal(10)**6)
                    with transaction.atomic():
                        user = get_object_or_404(User, wallet_address=backer)
                        pledged_project = get_object_or_404(Project, contract_id=campaign_id)                        
                        active_milestone = pledged_project.milestones.filter(status=Milestone.ACTIVE).first()
                        
                        # Create the donation record.
                        Donation.objects.create(
                            project=pledged_project, # Use pledged_project for consistency
                            user_profile=user.profile,
                            amount=net_amount,
                            tip=tip
                        )
                        
                        # Update the project's total funds.
                        pledged_project.total_funds += net_amount
                        pledged_project.save(update_fields=['total_funds'])
                        
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
                                                    
            except Exception as e:
                print(f"⚠️ Error processing log: {e}")
                print(f"Log data: {log}")

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': f'an error occurred: {e}'}, status=500)
