build:
	pipenv install;
	pipenv run cxfreeze --include-modules=discord,aiohttp,websockets,asyncio,asyncio.compat,asyncio.proactor_events,asyncio.base_events,asyncio.subprocess,asyncio.log,asyncio.tasks,asyncio.sslproto,asyncio.constants,asyncio.events,asyncio.base_tasks,asyncio.base_futures,asyncio.selector_events,asyncio.unix_events,asyncio.coroutines,asyncio.queues,asyncio.transports,asyncio.base_subprocess,asyncio.protocols,asyncio.windows_events,asyncio.locks,asyncio.compat,asyncio.futures,asyncio.windows_utils,asyncio.streams,asyncio.test_utils activityReader.py;
	pipenv run python build.py;
