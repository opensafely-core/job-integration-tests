# OpenSAFELY Job Orchestration example

This repository contains a docker-compose configuration suitable for
end-to-end testing of the job server components of the OpenSAFELY
framework.

Copy `env-sample` to `.env`, tweak as necessary (not required). Then
build and start the docker services with `./run_services.sh`, and run
`pytest` in a different console.
