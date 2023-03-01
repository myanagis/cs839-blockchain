#pylint: disable=missing-docstring,redefined-outer-name

import pytest
from eth_tester.exceptions import TransactionFailed

@pytest.fixture
def dao_contract(w3, get_vyper_contract):
    with open("dao.vy", encoding='utf-8') as infile:
        contract_code = infile.read()

    return get_vyper_contract(contract_code)

def test_nothing(dao_contract):
    pass

def test_buy_token(w3, dao_contract):
    account = w3.eth.accounts[7]
    assert dao_contract.balanceOf(account) == 0

    dao_contract.buyToken(transact={"from": account, "value": 1337})
    assert dao_contract.balanceOf(account) == 1337
    assert dao_contract.totalSupply() == 1337

def test_sell_token(w3, dao_contract):
    account = w3.eth.accounts[7]
    assert dao_contract.balanceOf(account) == 0

    dao_contract.buyToken(transact={"from": account, "value": 10101})
    dao_contract.sellToken(101, transact={"from": account})
    assert dao_contract.balanceOf(account) == 10000
    assert dao_contract.totalSupply() == 10000


def test_approve_with_single_voter(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    recipient = w3.eth.accounts[2]

    dao_contract.buyToken(transact={"from": account0, "value": 1337})

    initial_balance = w3.eth.getBalance(recipient)
    #assert initial_balance == 1337
    dao_contract.createProposal(1, recipient, 52, transact={"from": account0})
    #assert dao_contract.totalSupply() == 1337 #added
    assert w3.eth.getBalance(recipient) == initial_balance

    dao_contract.approveProposal(1, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance+52

def test_approve_with_transfer(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    account1 = w3.eth.accounts[6]
    recipient = w3.eth.accounts[2]

    # Give the majority of tokens to account1
    dao_contract.buyToken(transact={"from": account0, "value": 1337})
    dao_contract.transfer(account1, 1000, transact={"from": account0})

    initial_balance = w3.eth.getBalance(recipient)
    dao_contract.createProposal(1, recipient, 52, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance

    # account0's approval is not sufficient
    dao_contract.approveProposal(1, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance

    dao_contract.approveProposal(1, transact={"from": account1})
    assert w3.eth.getBalance(recipient) == initial_balance+52

def test_approve_unauthorized(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    recipient = w3.eth.accounts[9]

    dao_contract.createProposal(1, recipient, 52, transact={"from": account0})

    # Should not be allowed
    with pytest.raises(TransactionFailed):
        dao_contract.approveProposal(1, transact={"from": account0})

def test_approve_with_three_voters(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    account1 = w3.eth.accounts[2]
    account2 = w3.eth.accounts[4]

    recipient = '0xd3CdA913deB6f67967B99D67aCDFa1712C293601'

    dao_contract.buyToken(transact={"from": account0, "value": 25})
    dao_contract.buyToken(transact={"from": account1, "value": 30})
    dao_contract.buyToken(transact={"from": account2, "value": 45})

    assert dao_contract.totalSupply() == 100

    initial_balance = w3.eth.getBalance(recipient)
    prop_id = dao_contract.createProposal(1, recipient, 52, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance

    dao_contract.approveProposal(1, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance

    dao_contract.approveProposal(1, transact={"from": account1})
    assert w3.eth.getBalance(recipient) == initial_balance + 52
  
    # Additional votes will not transfer more money
    dao_contract.approveProposal(1, transact={"from": account2})
    assert w3.eth.getBalance(recipient) == initial_balance+52

def test_multiple_proposals(w3, dao_contract):
    account0 = w3.eth.accounts[7]

    recipient1 = w3.eth.accounts[1]
    recipient2 = w3.eth.accounts[2]

    dao_contract.buyToken(transact={"from": account0, "value": 1337})

    initial_balance1 = w3.eth.getBalance(recipient1)
    initial_balance2 = w3.eth.getBalance(recipient2)

    dao_contract.createProposal(42, recipient1, 11, transact={"from": account0})
    dao_contract.createProposal(37, recipient2, 14, transact={"from": account0})

    dao_contract.approveProposal(37, transact={"from": account0})
    assert w3.eth.getBalance(recipient1) == initial_balance1
    assert w3.eth.getBalance(recipient2) == initial_balance2+14

    dao_contract.approveProposal(42, transact={"from": account0})
    assert w3.eth.getBalance(recipient1) == initial_balance1+11
    assert w3.eth.getBalance(recipient2) == initial_balance2+14

def test_buy_tokens_multiple_times(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    account1 = w3.eth.accounts[2]

    recipient = '0xd3CdA913deB6f67967B99D67aCDFa1712C293601'

    dao_contract.buyToken(transact={"from": account0, "value": 25})
    dao_contract.buyToken(transact={"from": account1, "value": 30})
    dao_contract.buyToken(transact={"from": account0, "value": 45})

    assert dao_contract.totalSupply() == 100

    initial_balance = w3.eth.getBalance(recipient)
    dao_contract.createProposal(1, recipient, 52, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance

    dao_contract.approveProposal(1, transact={"from": account0})
    assert w3.eth.getBalance(recipient) == initial_balance + 52

def test_cannot_approve_twice(w3, dao_contract):
    account0 = w3.eth.accounts[7]
    recipient = w3.eth.accounts[0]

    dao_contract.buyToken(transact={"from": account0, "value": 1337})

    dao_contract.createProposal(1, recipient, 52, transact={"from": account0})
    dao_contract.approveProposal(1, transact={"from": account0})

    # Should not be allowed
    with pytest.raises(TransactionFailed):
        dao_contract.approveProposal(1, transact={"from": account0})