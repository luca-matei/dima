def application(env, start_response):
    response = lm.process.raw_request(env)

    start_response(str(response.status), response.headers)
    return [response.body]


lm.start()
