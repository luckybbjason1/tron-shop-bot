"""
TRON 결제 관리자 - USDT/TRX 검증
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TronPaymentManager:
    """TRON 블록체인 결제 관리자"""
    
    def __init__(self):
        self.network = os.getenv("TRON_NETWORK", "shasta")
        self.wallet_address = os.getenv("TRON_WALLET_ADDRESS", "")
        self.private_key = os.getenv("TRON_WALLET_PRIVATE_KEY", "")
        self.usdt_contract = os.getenv("USDT_CONTRACT_ADDRESS", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
        
        # 거래 내역 저장소
        self.pending_payments: Dict[str, dict] = {}
        self.completed_payments: Dict[str, dict] = {}
        
        # 트론 웹 초기화
        self.tron = None
        self.usdt_contract_obj = None
        self._initialize_tron()
    
    def _initialize_tron(self):
        """트론 객체 초기화"""
        try:
            from tronweb import TronWeb
            
            # 네트워크 설정
            if self.network == "mainnet":
                endpoint = "https://api.trongrid.io"
            elif self.network == "shasta":
                endpoint = "https://nile.trongrid.io"
            else:
                endpoint = "https://api.shasta.trongrid.io"
            
            self.tron = TronWeb(endpoint)
            
            if self.private_key:
                self.tron.setPrivateKey(self.private_key)
            
            # USDT 컨트랙트 로드
            self.usdt_contract_obj = self.tron.contract().at(self.usdt_contract)
            logger.info("TRON 네트워크 연결 완료")
            
        except Exception as e:
            logger.error(f"TRON 초기화 실패: {e}")
    
    def generate_payment_address(self, user_id: int, order_id: str) -> str:
        """지불 주소 생성 (더미 - 실제로는 서브 계정 생성 필요)"""
        # 실제 구현 시: TronWeb의 keyPair 생성 또는 서브 계정 사용
        return self.wallet_address
    
    def create_payment_request(self, user_id: int, product_id: int, 
                               amount: float, currency: str) -> dict:
        """결제 요청 생성"""
        import hashlib
        
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{hashlib.md5(str(user_id).encode()).hexdigest()[:6]}"
        
        payment = {
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "amount": amount,
            "currency": currency,
            "payment_address": self.wallet_address,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "transaction_hash": None
        }
        
        self.pending_payments[order_id] = payment
        logger.info(f"결제 요청 생성: {order_id}, 금액: {amount} {currency}")
        
        return payment
    
    def check_payment_status(self, order_id: str) -> dict:
        """결제 상태 확인"""
        # 보류 중
        if order_id in self.pending_payments:
            payment = self.pending_payments[order_id]
            if payment["status"] == "pending":
                # 트론 블록체인에서 거래 확인
                self._check_blockchain_payment(order_id)
        
        # 완료됨
        if order_id in self.completed_payments:
            return self.completed_payments[order_id]
        
        return {"status": "not_found"}
    
    def _check_blockchain_payment(self, order_id: str):
        """블록체인에서 결제 확인"""
        if not self.tron or not self.usdt_contract_obj:
            logger.warning("TRON 객체 없음 - 블록체인 확인 건너뜀")
            return
        
        try:
            payment = self.pending_payments[order_id]
            amount_wei = int(payment["amount"] * 10**6) if payment["currency"] == "USDT" else int(payment["amount"] * 10**6)
            
            # USDT 잔고 확인 (실제 구현은 더 복잡)
            # 현재는 더미 체크 (모의 테스트용)
            logger.info(f"결제 확인 중: {order_id}")
            
            # 실제로는 트랜잭션 해시로 검증해야 함
            # self.tron.trx.get_transaction(payment["transaction_hash"])
            
        except Exception as e:
            logger.error(f"블록체인 확인 오류: {e}")
    
    def confirm_payment(self, order_id: str, transaction_hash: str) -> bool:
        """결제 확인"""
        if order_id in self.pending_payments:
            payment = self.pending_payments[order_id]
            payment["status"] = "paid"
            payment["transaction_hash"] = transaction_hash
            payment["paid_at"] = datetime.now().isoformat()
            
            # 완료된_payments로 이동
            self.completed_payments[order_id] = payment
            del self.pending_payments[order_id]
            
            logger.info(f"결제 확인 완료: {order_id}, TX: {transaction_hash}")
            return True
        return False
    
    def verify_transaction(self, tx_hash: str) -> bool:
        """트랜잭션 검증"""
        if not self.tron:
            return False
        
        try:
            tx = self.tron.trx.get_transaction(tx_hash)
            if tx and tx.get("ret"):
                # 성공적인 트랜잭션
                return True
            return False
        except Exception as e:
            logger.error(f"트랜잭션 검증 오류: {e}")
            return False
    
    def get_wallet_balance(self) -> dict:
        """지갑 잔고 확인"""
        if not self.tron:
            return {"error": "TRON not initialized"}
        
        try:
            # TRX 잔고
            trx_balance = self.tron.trx.get_balance(self.wallet_address)
            
            # USDT 잔고
            usdt_balance = 0
            if self.usdt_contract_obj:
                usdt_balance = self.usdt_contract_obj.balanceOf(self.wallet_address).call()
                usdt_balance = usdt_balance / 10**6  # 6자리 소수점
            
            return {
                "trx": trx_balance / 10**6,
                "usdt": usdt_balance,
                "address": self.wallet_address
            }
        except Exception as e:
            logger.error(f"잔고 확인 오류: {e}")
            return {"error": str(e)}

# 전역 인스턴스
payment_manager = None

def get_payment_manager() -> TronPaymentManager:
    global payment_manager
    if payment_manager is None:
        payment_manager = TronPaymentManager()
    return payment_manager
