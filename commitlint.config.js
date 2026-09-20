/**
 * Sentinel — Configuration commitlint
 * Convention : Conventional Commits
 * Types autorisés alignés sur la section 13 du README.
 */
export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "refactor",
        "docs",
        "test",
        "chore",
        "security",
        "perf",
        "ci",
        "build",
        "revert",
      ],
    ],
    "subject-case": [0],
    "header-max-length": [2, "always", 100],
  },
};
