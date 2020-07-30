# OpenSAFELY Job Orchestration example

This repository contains a docker-compose configuration suitable for
end-to-end testing of the job server components of the OpenSAFELY
framework.

Copy `env-sample` to `.env`, tweak as necessary (not required). Then:

    docker-compose build --build-arg pythonversion=3.8.1  && docker-compose up

Now run `pytest`
