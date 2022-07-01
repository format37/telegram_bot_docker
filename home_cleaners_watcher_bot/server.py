from urllib import response
from aiohttp import web
import json
import os
import pandas as pd


def cleaner_bot_counter_plus(account_id,task):
    df_full = pd.read_csv('data/data.csv')
    current_value = int(df_full[df_full.account_id==account_id][task])
    df_task = df_full[['account_id', task]]

    # Economics ++
    account_value = float(df_task[df_task.account_id==account_id][task])
    appendix = 1
    if len(df_task)>1 and account_value>df_task[task].min():
        for idx,row in df_task.iterrows():
            if account_value>row[task]:
                appendix += (account_value-row[task])/10
    # Economics --

    df_full.loc[(df_full.account_id==account_id),task]=current_value+round(appendix,1)
    df_full.to_csv('data/data.csv',index = None)
    return task+' +'+str(round(appendix,1))


def cleaner_bot_counter_minus(account_id,task):	
	df_full = pd.read_csv('data/data.csv')
	if task in df_full.columns:
		current_value = int(df_full[df_full.account_id==account_id][task])
		df_full.loc[(df_full.account_id==account_id),task]=current_value-1
		df_full.to_csv('data/data.csv',index = None)
		answer = task+' -1'
	else:
		answer = 'task not found: "'+task+'"'
	return answer


def cleaner_bot_user_authorized(account_id):
	df_full = pd.read_csv('data/data.csv')
	return str(account_id) in [str(i) for i in df_full.account_id.to_list()]


async def call_message(request):
    cleaning_group_id = '-37549110'
    # load data
    data = json.loads(await request.json())
    message = str(data['message'])
    group = str(data['group'])
    user = str(data['user'])

    if not cleaner_bot_user_authorized(user):
        return web.Response(text='User not authorized')

    answer = 'Command not found'

    # extract command from message
    # for example, message:
    # /dish@home_cleaners_watcher_bot
    # command:
    # dish
    task = message.split('@')[0].split('/')[1]    
    if group == cleaning_group_id:
        if task in ['dish', 'garbage', 'toilet', 'dry']:
            answer = cleaner_bot_counter_plus(int(user), task)

        if task == 'cancel':
            # extract thing to cancel from message
            # for example, message:
            # /cancel dish
            # thing:
            # dish
            thing = message.split(' ')[1]
            answer = cleaner_bot_counter_minus(int(user), thing)
    
    return web.Response(text=answer, content_type='application/json')


def main():
    app = web.Application(client_max_size=1024**3)
    app.router.add_route('POST', '/message', call_message)    
    web.run_app(app, port=os.environ.get('PORT', ''))


if __name__ == "__main__":
    main()
