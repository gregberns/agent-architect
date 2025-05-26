/** @type {import('jest').Config} */
const config = {
  // shut up "jest-haste-map: Haste module naming collision: ..." since jest is being 'helpful' and deeply scanning a bunch of directories it doesn't need to.   modulePathIgnorePatterns: ['<rootDir>/.opam_root/', '<rootDir>/.yarncache/', '<rootDir>/_opam/'],
  modulePathIgnorePatterns: ['<rootDir>/.opam_root/', '<rootDir>/.yarncache/', '<rootDir>/_opam/'],
  testEnvironment: 'node',
  testRegex: '_build/default/.*/src/.*/__tests__/.*Tests\\.js?$|.*/test/.*\\.test\\.js',
};

module.exports = config;
