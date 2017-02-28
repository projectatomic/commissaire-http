# commissaire-http v0.0.2
```
* cf42758: handlers: Fix container manager routes.
* 0dacbbb: handlers: Include 'container_manager' data in host status.
* f39dde2: handlers: Call 'container.remove_node' when deleting a cluster member.
* 60be29d: handlers: Call 'container.remove_all_nodes' when deleting cluster.
* f15676d: handlers: Call 'container.remove_node' when deleting host.
* 606683e: Use commissaire.util.config.import_plugin()
* 51c7b51: handlers: Fix usage of an invalid error code.
* 5064ddb: handlers: Fix logging typo in JSONRPC_Handler.
* 9da5131: handlers: Add decorators to handler functions.
* e6db041: dispatcher: Move get_params() to handlers.
* ea2e75b: dispatcher: Add routematch results to environment.
* e7ff55e: dispatcher: Move parse_query_string() to handlers.
* 16bde8f: handlers: Rename return_error().
* 5d11bc7: handlers: Rename create_response().
* ce498b6: handlers: Don't use create_response() in exception handlers.
* fe5529e: Host creation now sends container_manager data.
* 2093f83: Registered container manager endpoints.
* afc11e6: constants: Remove JSONRPC_ERRORS['NOT_FOUND'] alias.
* 44554e1: dispatcher: Add setup_bus() method.
* 27b58ff: dispatch: Maybe not introduce a massive security hole.
* 1387e85: dispatcher: Handle bad input params as 400 Bad Request
* a08179a: handlers: Fix bug in get_cluster().
* 8745b0c: handlers: Catch StorageLookupError.
* 04e48f4: dispatcher: Log traceback when handler throws exception.
* 10936c3: handlers: Simplified host_create.
* 6b80741: bug: Fixed delete_host when host is not in a cluster.
* 2aab641: handlers: get_cluster now uses constants.
* f11e09e: Adapt to logging configuration changes.
* 03caf85: dispatcher: Use 'action' verbs in route to tweak status codes.
* 838af8c: handlers: Connect route for update_cluster_members.
* 8813ccd: dispatcher: Return 201 on successful PUT requests.
* 42c7d43: dispatcher: Bus injection now easier and enforced.
* 09670d7: server: Added better bus creation logging.
* 81a01fe: Use StorageClient to talk to storage service.
* 10c0984: Use appropriate to_dict() or to_json() calls.
* b4f83b2: Invoke cluster operations on jobs.clusterexec.
* a8f53b3: Container manager endpoints (#44)
* 4c3cf9a: Implement logging from commissaire common lib
* 3bab0cf: Cluster operation endpoints (#41)
* 838a073: Merge pull request #36 from ashcrow/systemd
* ed490f3: auth: Stacked complex plugins no longer have to be last. (#39)
* 6364bec: AuthenticationManager: Simplify authentication loop.
* e268c2a: auth: add try/except to AuthN flow
* 97655ef: auth: return the subject token for authn use
* 1bf2e7d: auth: add testcases for keystone token authn
* 7dca31b: auth: keystone token authentication
* 7c6b068: systemd: Added unit file.
* 7788ce4: cli: AuthenticationManager can now be used via the CLI.
* 1f633c0: test: AuthenticationManager and FakeStartResponse.
* 49e036a: auth: AuthN now occurs via the AuthenticationManager.
* dec862c: auth: Direct responses now merge headers.
* ae4b57e: bug: FakeStartResponse call_count was not incrementing.
* 2ab4979: util: Added wsgi util with FakeStartResponse.
* b5a142b: auth: Clarified direct response pattern.
* 806064b: auth: Plugins can now handle responses directly.
* d1c3f6d: test: Added success/failure for base authenticator.
* 6380ded: test: Added a dummy wsgi app for authenticator.
* 3f00db0: test: httpbasicauth test clean up.
* dc3ab6f: Add license header
* 6ebc29d: auth: KeystonePassword auth fails early on missing data.
* c926419: test: Added tests for keystonepasswordauth.
* 0c07b5f: Implement AuthN against OpenStack Keystone using password method #21
* 9d22666: handlers: create_host adds host to the watcher queue. (#30)
* db251b7: handlers: create_host now notifies the investigator. (#27)
* c4194fc: build: requirements files now list licenses.
* cad17f6: .redhat-ci.yml: switch to containerized builds
* c9597ba: handlers: Added cluster_delete. (#24)
* 5ffc080: docs: Added Gerard Braad to CONTRIBUTORS.
* da503c0: Reformat Dockerfile and remove redundant clean call
* f339bea: Idea: Handler registration (#19)
* a2b1485: test: simplified network tests.
* 309d6b9: test: simplified cluster tests.
* ee649fa: routing: Added optional_slashes. (#16)
* deed959: Add Host Endpoints (#15)
* 0c83d54: tests: Simplified network tests.
* b13eb3a: handlers: Added delete_network.
* e6fb4cd: handlers: Added create_network.
* 925a8f9: handlers: Added get_network.
* 9cb6358: handlers: Added list_networks.
* 270a800: git: Added nosetests.html to ignore.
* ab97b7c: Cluster endpoints (#8)
* 738da48: test: Updates to enable redhat-ci.
* 3f619d9: test: Added nose-htmloutput to test requirements.
* d984e80: dispatcher: Added _get_params to simplify dispatch.
* 44be95e: constants: Add JSONRPC constants.
* 03ffacb: dispatcher: Now handles jsonrpc error code -32602 responses. (#10)
* 7fa832c: handlers: Added LOGGER for use in handlers.
* fcf2af3: dispatcher: Now supports passing URI params.
* 0d3f733: Initial Docker File and Setup Fix (#7)
* 54b38c0: Basic Server Port (#6)
* 3b5bc74: test: Updated repo for Travis/Jenkins CI usage through tox. (#5)
* 06de004: handlers: Added cluster listing.
* 6476bba: build: Added commissaire to the requirements file.
* cd409c7: bug: Typo fix.
* 735bf14: Bus now takes advantage of commissaire.bus.BusMixin.
* e082604: auth: Ported basic and cert authentication.
* fa33a2f: test: Ported get_fixture_file_path to test.
* 470e74c: SSL_CLIENT_VERIFY now passed in WSGI env.
* 546f1ae: setup: Updated complexity threshold.
* 83410de: Added bus interface.
* 51faf07: example: Simplified logging section.
* 49c2778: doc: Updated README.md wording.
* 52ecfba: test: Added basic unittests.
* d612471: Moving to jsonrpc handlers.
* f84f54e: Now using routes for routing.
* 299b536: Switched to jsonrpc message format.
* 40d0235: Simplified API for topic usage.
* 4fd9b99: Moved to topic in example.
* ab906cb: dispatcher: Updated for actions message format.
* af55d55: Added no_data and bad gateway support.
* 0fa4b4a: Added TLS support.
```
