# Known Issues

- Legacy UI, gem and audio asset provenance still requires owner review. Entries are marked
  `LicenseRef-PendingReview`; this blocks GA but not local development or automated tests.
- The gameplay screen migration to the controller boundary is incremental; legacy Kivy
  orchestration remains until the Day 4 integration spike and hard contract freeze.
- Balance version `v1` is the only evaluator implementation in app version 0.1.0.
