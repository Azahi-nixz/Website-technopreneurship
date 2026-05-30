import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    // Each property-based test (fast-check) runs with a minimum of 100 examples.
    // Individual test files can override this via fc.configureGlobal().
    setupFiles: [],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['app/static/js/**/*.js'],
    },
  },
})
