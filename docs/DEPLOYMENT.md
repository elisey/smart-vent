# Deployment Guide

This document describes how to deploy the Smart Ventilation Controller component to production Home Assistant instances.

## Repository Structure

This repository follows the standard HACS-compatible structure:

```
ha-dev/
├── custom_components/
│   └── smart_vent/           # The actual integration code (deployed to users)
├── config/                   # Development HA configuration (not deployed)
├── docker-compose.yaml       # Development infrastructure (not deployed)
├── docs/                     # Documentation (not deployed)
├── test_service.py           # Development tools (not deployed)
├── README.md                 # Shown in HACS UI
└── hacs.json                 # HACS metadata (optional)
```

**Key point:** Only `custom_components/smart_vent/` is deployed to users. Everything else is development infrastructure.

## Deployment Methods

### Method 1: Direct Git Clone with Symlink (Simplest for personal use)

On your production HA machine:

```bash
# Clone the repository somewhere convenient
cd ~
git clone https://github.com/your-username/ha-dev.git

# Create symlink in HA config
ln -s ~/ha-dev/custom_components/smart_vent /path/to/homeassistant/config/custom_components/smart_vent

# Restart Home Assistant
```

**Updating:**
```bash
cd ~/ha-dev
git pull
# Restart Home Assistant
```

**Pros:**
- Simple and straightforward
- Easy to update
- Can access development tools if needed

**Cons:**
- Manual restart required
- Requires SSH access to production machine

### Method 2: HACS Custom Repository (Recommended for production)

This method allows you to use HACS UI to install and update the component without SSH access.

#### Initial Setup

1. **Create `hacs.json` in repository root:**

```json
{
  "name": "Smart Ventilation Controller",
  "render_readme": true
}
```

2. **Create a GitHub Release:**

```bash
# Tag the current version
git tag v0.1.0
git push origin v0.1.0

# Or create release via GitHub UI:
# Go to: Releases → Create a new release
# Tag: v0.1.0
# Title: v0.1.0
# Description: Initial release
```

3. **Add to HACS as Custom Repository:**

In Home Assistant:
- Go to HACS
- Click ⋮ (three dots menu)
- Select "Custom repositories"
- Add repository URL: `https://github.com/your-username/ha-dev`
- Select category: "Integration"
- Click "Add"

4. **Install via HACS:**

- Go to HACS → Integrations
- Search for "Smart Ventilation Controller"
- Click "Download"
- Restart Home Assistant

#### Updating via HACS

When you push updates:

1. Create a new release on GitHub:
```bash
git tag v0.2.0
git push origin v0.2.0
```

2. In HACS:
- The component will show an update available
- Click "Update"
- Restart Home Assistant

**Pros:**
- Works on all HA installations (including Supervised/OS without SSH)
- Updates via UI
- Proper version management
- Can share with others easily

**Cons:**
- Requires creating GitHub releases
- Slightly more initial setup

### Method 3: HACS Official Repository (Future)

To be included in the official HACS default repository, you need to meet additional requirements:

**Required:**
- Public GitHub repository
- Repository description
- README.md with usage instructions
- At least one release
- Repository added to [home-assistant/brands](https://github.com/home-assistant/brands)
- Repository topics/tags for searchability
- Only one integration per repository
- All files in `custom_components/integration_name/`

**Process:**
1. Ensure all requirements are met
2. Submit PR to [hacs/default](https://github.com/hacs/default)
3. Wait for review and approval

Once approved, users can find and install the component directly from HACS without adding a custom repository.

## How HACS Deployment Works

When HACS installs a component:

1. Clones the GitHub repository to a temporary location
2. Copies **only** the contents of `custom_components/smart_vent/` to `/config/custom_components/smart_vent/`
3. Deletes the temporary clone

This means:
- Users don't get `docker-compose.yaml`, `config/`, `docs/`, or any development files
- The repository can contain as much development infrastructure as needed
- Only the integration code is deployed

## Version Management

Update the version in `custom_components/smart_vent/manifest.json` before creating a new release:

```json
{
  "domain": "smart_vent",
  "name": "Smart Ventilation Controller",
  "version": "0.2.0",  // Update this
  "documentation": "https://github.com/your-username/ha-dev",
  "requirements": [],
  "dependencies": [],
  "codeowners": [],
  "iot_class": "local_polling"
}
```

Version should match the git tag (without the 'v' prefix).

## Best Practices

1. **Always test locally** using docker-compose setup before creating a release
2. **Use semantic versioning**: MAJOR.MINOR.PATCH (e.g., 0.1.0, 0.2.0, 1.0.0)
3. **Write release notes** describing changes in each GitHub release
4. **Update README.md** with any configuration changes
5. **Keep manifest.json version in sync** with git tags

## Troubleshooting

### Component not appearing in HACS after adding custom repository
- Ensure you have at least one GitHub release
- Check that `manifest.json` is valid JSON
- Verify repository URL is correct
- Try removing and re-adding the custom repository

### Updates not showing in HACS
- Ensure you created a new git tag and pushed it: `git push origin v0.x.x`
- Wait a few minutes for HACS to check for updates
- Try clicking "Redownload" in HACS

### Component not loading after installation
- Check Home Assistant logs for errors
- Verify all required files are in `custom_components/smart_vent/`
- Ensure `manifest.json` has correct domain name
- Restart Home Assistant after installation

## References

- [HACS Documentation](https://hacs.xyz/docs/publish/integration/)
- [Home Assistant Integration Development](https://developers.home-assistant.io/)
- [HACS Custom Repositories](https://www.hacs.xyz/docs/faq/custom_repositories/)
