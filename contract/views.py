from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import json
from .blockchain import contract, send_owner_tx
from web3 import Web3 


# def approve_milestone(campaign_id: int, index: int):
#     return send_owner_tx(contract.functions.approveMilestone(campaign_id, index))

# def withdraw_milestone(campaign_id: int, index: int):
#     return send_owner_tx(contract.functions.withdrawMilestone(campaign_id, index))


# def finalize_campaign(campaign_id: int):
#     return send_owner_tx(contract.functions.finalize(campaign_id))





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
        token = Web3.to_checksum_address(token)
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

