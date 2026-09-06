.PHONY: bootstrap-check extraction-check validate

bootstrap-check:
	./scripts/bootstrap_validate.sh .

extraction-check:
	./scripts/verify_extraction.sh .

validate: bootstrap-check
	@if [ -f ops/bin/rpi5-update ]; then ./scripts/verify_extraction.sh .; else echo "source extraction not present yet; bootstrap-only validation"; fi
