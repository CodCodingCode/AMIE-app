import { defineConfig } from 'eslint-define-config';
import nextPlugin from '@next/eslint-plugin-next';

export default defineConfig({
  root: true,
  plugins: {
    '@next/next': nextPlugin
  },
  extends: [
    'eslint:recommended',
    'plugin:@next/next/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  rules: {
    'react/react-in-jsx-scope': 'off'
  }
});
