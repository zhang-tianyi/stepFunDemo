import requests
import os
from typing import Optional, Dict, Any


def query_voices(
    api_key: str,
    base_url: str,
    limit: Optional[int] = None,
    order: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询当前用户下的复刻音色（纯函数实现）
    
    :param api_key: API访问令牌
    :param base_url: API基础地址
    :param limit: 分页数量，默认20，最大100，最小1
    :param order: 排序方式，asc(升序)或desc(降序)
    :param before: 分页指针ID（之前）
    :param after: 分页指针ID（之后）
    :return: 包含音色信息的字典
    """
    url = f"{base_url}/audio/voices"
    
    # 处理参数边界
    params = {}
    if limit is not None:
        params['limit'] = max(1, min(100, limit))  # 确保在1-100范围内
    if order in ['asc', 'desc']:
        params['order'] = order
    if before:
        params['before'] = before
    if after:
        params['after'] = after
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 抛出HTTP错误状态码
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        if 'response' in locals():
            print(f"状态码: {response.status_code}, 响应内容: {response.text}")
        raise

# 测试样例执行部分
if __name__ == "__main__":
    try:
        # 读取配置
        api_key = os.environ["STEPFUN_API_KEY"]
        base_url= os.environ['STEPFUN_ENDPOINT']

        # 调用查询函数（可根据需要调整参数）
        voices = query_voices(
            api_key=api_key,
            base_url=base_url,
            limit=10,
            order='desc'
        )
        
        # 打印测试结果
        print(f"测试结果 - 总音色数: {len(voices.get('data', []))}")
        print(f"是否有更多数据: {voices.get('has_more', False)}")
        for idx, voice in enumerate(voices.get('data', []), 1):
            print(f"\n音色 {idx}:")
            print(f"ID: {voice.get('id')}")
            print(f"源文件ID: {voice.get('file_id')}")
            print(f"创建时间: {voice.get('created_at')}")
            
    except Exception as e:
        print(f"测试执行失败: {e}")