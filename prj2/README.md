# A Decentralized Autonomous Organization

In this project we aim to build a simplified version of DAO.

There are two functionalities to implement.

## Shareholding
People can pay into the DAO and receive a custom token.
Their token balance enables them to vote and determines their voting power.

The contract supports the ERC20 interface, so that the token can be traded like any other token.
You need to implement all functions that are defined by the ERC20 to do this.
For example, one can give other accounts an allowance to transfer tokens for you.

You can take a look at the [ER20 sample contract](https://github.com/vyperlang/vyper/blob/master/examples/tokens/ERC20.vy) sample contract in the Vyper repository.
It is fine to copy some of that code.
Note, that you do not need to implement ERC20Detailed, just ERC20.

You need to implement a `buyToken` and `sellToken` method that convert Ether into the token and vice versa.

## Voting
The voting process has two steps.

First, someone has to create a *proposal*. For simplicity, a proposal consists of just an address and an integer value `i`.
If the proposal succeeds, `i` Ether will be transferred to the specified address.

The function to create a proposal is listed below.
The first argument is a unique identifier (pick a random number) for the proposal.
The call should fail if the UID is already in use or if the amount specified is zero.

```vyper
def createProposal(_uid: uint256, _recipient: address, _amount: uint256)
```

Second, stakeholders need to *approve* a proposal.
For a proposal to succeed, the yes votes must represent a majority of the stake, not just the stakeholder.
Again, for simplicity, proposals do not expire, and you do not need to implement no votes.
You can also assume that no new tokens are issued while the voting occurs.

The voting mechanism then just takes the proposal identifier as an argument and must be sent from a stakeholders account.
If the entity calling the function is not a stakeholder, the transaction should be reverted.
Similarly, if the caller already voted the call should fail.

```vyper
def approveProposal(_proposal_id: uint256)
```

## Simplifications

* You do not need to handle the case where a proposal asks for more money than it is stored in the contract. We will not test for this.

* `sellToken` in this form would not exist in a real DAO. You also do not need to handle the case where the DAO does not have enough money to execute `sellToken`.
