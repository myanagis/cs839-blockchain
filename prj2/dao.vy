from vyper.interfaces import ERC20

implements: ERC20




event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

# from https://eips.ethereum.org/EIPS/eip-20: we need to add: transfer, transferFrom, approve to comply with interface


@external
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value

    log Transfer(msg.sender, _to, _value)
    return True
    
@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    # NOTE: vyper does not allow underflows
    #      so the following subtraction would revert on insufficient allowance
    self.allowance[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
         Beware that changing an allowance with this method brings the risk that someone may use both the old
         and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
         race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will spend the funds.
    @param _value The amount of tokens to be spent.
    """
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True


# these are all already public getters
# see: https://github.com/vyperlang/vyper/blob/master/examples/tokens/ERC20.vy
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
stakeholders: public(DynArray[address, 10]) # allow, arbitrarily, up to 10 stakeholders


# here's where we store it on the contract
# This is a type for a list of proposals.
#proposals: public({
#    # short name
#    name: uint256,
#    vote_count: uint256,
#    voted: address[10], 
#    amount_recipient: address,
#    amount: uint256
#}[uint256])




@external
def __init__():
    self.totalSupply = 0

###### Buying/selling

@external
@payable
@nonreentrant("lock")
def buyToken() -> bool:
    # increase the user's balance
    val: uint256 = msg.value
    self.balanceOf[msg.sender] += val
    
    # add value of bought token to the tracker
    
    #TODO: 1. Check if the array below already contains the sender. (e.g. if user buys tokens twice, he'll be listed 2x)
    #      2. if user sells all their shares, then delist from stakeholders
    length: uint256 = len(self.stakeholders)
    self.stakeholders.append(msg.sender)
    
    # increase total supply
    self.totalSupply += msg.value
    return True

@external
@nonreentrant("lock")
def sellToken(_value: uint256) -> bool:
    #TODO: check if the user actually has this balance to sell
    
    # decrement from user
    self.balanceOf[msg.sender] -= _value
    
    # decrement from total supply
    self.totalSupply -= _value
    
    return True




######VOTING

# some of this from https://docs.vyperlang.org/en/v0.1.0-beta.2/vyper-by-example.html#voting


proposals: public(uint256[100])
proposals_recipient: public(HashMap[uint256, address])
proposals_recipient_amount: public(HashMap[uint256, uint256])
proposals_voted: public(HashMap[uint256, address[10]])
proposals_weight_approved: public(HashMap[uint256, uint256])
proposals_is_approved: public(HashMap[uint256, bool])

@external
def createProposal(_proposal_id: uint256, _recipient: address, _amount: uint256) -> uint256:
    
    # checks
    #if self.proposals[_proposal_id] != 0:
    #    raise "Proposal ID already taken"
    if _amount <= 0:
        raise "Proposal amount is zero or less! Not creating this"
    
    # add the proposal info 
    # this is a terrible implementation
    self.proposals_recipient[_proposal_id] = _recipient
    self.proposals_recipient_amount[_proposal_id] = _amount
    
    return 1

@external
def approveProposal(_proposal_id: uint256):

    # get sender amount
    approver_amount: uint256 = self.balanceOf[msg.sender]


    # checks
    # check if the sender actually has any stake in this game (i.e. valid stakeholder)
    if approver_amount == 0:
        raise 'invalid transaction'

    # check that the user didn't already vote
    did_user_already_vote: bool = False
    already_voted: address[10] = self.proposals_voted[_proposal_id]
    for i in range(10):
        v:address = already_voted[i]
        if v == msg.sender:
            raise 'already voted'

    # otherwise, add the person
    for i in range(10):
        v: address = already_voted[i]
        if v == ZERO_ADDRESS:
            already_voted[i] = msg.sender
            break
    self.proposals_voted[_proposal_id] = already_voted



    # increment amount that is approved
    self.proposals_weight_approved[_proposal_id] += approver_amount

    
    # if there is > 50%, then approve it
    total_approved: uint256 = self.proposals_weight_approved[_proposal_id]
    if (2*total_approved) >= self.totalSupply:

        if self.proposals_is_approved[_proposal_id] != True:
            # transfer the dough
            recipient: address = self.proposals_recipient[_proposal_id]
            amount_to_send: uint256 = self.proposals_recipient_amount[_proposal_id]
            send(recipient, amount_to_send) #amount_to_send)

            # mark contract as approved
            self.proposals_is_approved[_proposal_id] = True

