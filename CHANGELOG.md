# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.5.6] - 2024-03-02

### Added
- [Client.login_secret](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L301) method created

### Changed
- removed `secret` parameter from [Client.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L258)
  and [AsyncClient.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_async/client.py#L258) methods
- `email` and `password` parameters of [Client.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_sync/client.py#L258)
  and [AsyncClient.login](https://github.com/kwel999/K_Amino/blob/a19b070d35e0a9d51d3538640cc7650273733ce2/k_amino/k_async/client.py#L301) methods are now required
