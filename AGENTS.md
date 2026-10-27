# AGENTS.md

This repo is the SoloHost package skill. If you were asked to build a SoloHost package
(the `docker-compose.yml` + `config_options.yml` pair for an app with a public Docker
image), follow [`skills/solohost-package/SKILL.md`](skills/solohost-package/SKILL.md)
step by step. Write the package into a new folder outside `skills/`.

- Rules: [`skills/solohost-package/references/contract.md`](skills/solohost-package/references/contract.md)
- Install-form fields: [`skills/solohost-package/references/config-options.md`](skills/solohost-package/references/config-options.md)
- Examples: [`skills/solohost-package/examples/`](skills/solohost-package/examples/)
- Validator: `python3 skills/solohost-package/scripts/validate_api.py <package-dir>`

If you are changing the skill itself, read [`CONTRIBUTING.md`](CONTRIBUTING.md) first.
