from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
# .models에서 User 모델을 가져옴 (현재 코드에서 직접 쓰이지 않지만 확장을 위한 존재)
from .models import User

# /account 경로로 시작하는 API 그룹 생성
router = APIRouter(prefix="/account")

@router.get("/users/{username}")
async def user_detail(username: str) -> dict:
    """
    특정 사용자 정보를 조회하는 API 엔드 포인트
    - username: URL 경로 파라미터로 받은 사용자 아이디
    """
    # 임시 데이터 처리 (보통은 여기서 DB 조회를 합니다)
    if username == "test":
        return {
            "id": 1,
            "username": username,
            "email": f"{username}@example.com",
            "display_name": username,
            "is_host": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    # 해당 사용자가 없을 경우 404 에러 발생
    raise HTTPException(
        status_code =status.HTTP_404_NOT_FOUND, 
        detail="User not found"
    )
