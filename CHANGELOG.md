# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.6.1] - 2024-03-17

### Added
- [PayloadTooLarge](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/lib/exception.py#L106) : created to catch errors, when the request body lenght exceeds the API limit

### Fixed
- [upload_media](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/k_sync/client.py#L450) : problems
  with `Content-Length` header and request body

### Changed
- [upload_media](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/k_sync/client.py#L450) : now supports `file` of type `bytes`
- [app_headers](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/lib/headers.py#L124) : The
  type of the `data` parameter was changed to `bytes | None`
- [generateSig](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/lib/util.py#L57): now
  supports `data` of type `bytes`
- [check_server_exceptions](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/lib/exception.py#L191) : now returns a subclass object of `ServerError`
- [check_exceptions](https://github.com/kwel999/K_Amino/blob/46e0b5874cade8143e906623780231d0139b1f3e/k_amino/lib/exception.py#L201) : now returns a subclass object of `APIError`

### Removed
- [UnknownException](https://github.com/kwel999/K_Amino/blob/4bc072fe2915c12997e932586f85e3de472f3514/k_amino/lib/exception.py#L9) : removed
  because it is caught by the `APIError` base class

## [1.6.0] - 2024-03-16

### Changed
- the `send_message` method supports video messages
- Added `fileCoverImage` parameter to `send_message` method

## [1.5.5.7] - 2024-03-03

### Fixed
- [Wss.ws_task](https://github.com/kwel999/K_Amino/blob/b613bea3ac684032c47f94a5d71456898696763b/k_amino/k_sync/sockets.py#L843) : socket reconnection problems when a frame error occurs

## [1.5.5.6] - 2024-03-02

### Added
- [Client.login_secret](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L301) : method created

### Changed
- removed `secret` parameter from [Client.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L258)
  and [AsyncClient.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_async/client.py#L258) methods
- `email` and `password` parameters of [Client.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L258)
  and [AsyncClient.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_async/client.py#L301) methods are now required
