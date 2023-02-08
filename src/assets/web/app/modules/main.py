def application(env, start_response):
    response = lm.process.request(env)

    start_response(str(response.status), response.headers)
    return [response.body]


lm.start()
