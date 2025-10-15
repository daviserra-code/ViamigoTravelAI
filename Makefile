            .PHONY: install dev build start lint format clean

            install:
	npm ci

            dev:
	npm run dev

            build:
	npm run build

            start:
	npm start

            lint:
	npm run lint || true

            format:
	npm run format || true

            clean:
	rm -rf node_modules .next dist build
