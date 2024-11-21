import aiohttp

class RequestTask():
    
    async def async_fetch_get(api_endpoint, headers, username, password):
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint, headers=headers, auth=aiohttp.BasicAuth(username, password), verify_ssl=False) as response:
                return await response.json()
            
    async def async_fetch_post(api_endpoint, data, headers, username, password):

        auth = aiohttp.BasicAuth(username, password)
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(api_endpoint, json=data, headers=headers, verify_ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ошибка: {response.status}")
