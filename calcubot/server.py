from aiohttp import web
import os


async def call_message(request):
    data = await request.json()
    message = data['message']+'W'
    return web.Response(text=message)


def main():
    app = web.Application(client_max_size=1024**3)    
    app.router.add_route('POST', '/message', call_message)    
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
