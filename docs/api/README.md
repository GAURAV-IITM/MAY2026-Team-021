# API Documentation

`openapi.yaml` will be the reviewed Swagger-compatible contract for Milestones
3 and 4.

Workflow:

1. Update the YAML and user-story mapping before implementing an endpoint.
2. Review request fields, responses, error cases, roles, and tenant behavior.
3. Implement the matching FastAPI route and pytest cases.
4. Compare the running FastAPI OpenAPI schema with the checked-in contract.
5. Commit contract and implementation changes in the same pull request.

Each operation should include:

- a stable `operationId`;
- summary and description;
- user-story reference using an `x-user-stories` extension;
- authentication and role expectations;
- parameters or request body;
- success response;
- validation, authentication, permission, not-found, and conflict responses
  where applicable;
- example input and output.

The final YAML must validate as OpenAPI 3.x and match the submitted revision.
