import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from unittest.mock import MagicMock, patch
import SaaS

@pytest.mark.asyncio
async def test_trip_date_parsing():
    # 직원목록 더미 방지(people_list 파라미터 제거)
    with patch.object(SaaS, 'notion', autospec=True) as mock_create:
        mock_create.pages.create = MagicMock()
        await SaaS.create_dummy_data('db_id', '출장 요청서')
        # 더미 5건 생성되는지
        assert mock_create.call_count == 5
        # 첫 호출의 날짜 파싱 확인
        first_call = mock_create.call_args_list[0]
        props = first_call.kwargs['properties']
        assert props['출장기간']['date']['start'] == '2024-06-01'
        assert props['출장기간']['date']['end'] == '2024-06-05'