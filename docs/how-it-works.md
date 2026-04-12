# How it works

The **raccoonz** workflow follows these steps:
- **sniff**: match a URL to a known local [bin](glossary.md#bin) endpoint
- **forage**: if no local match, search for a remote bin
- **learn**: if a remote bin matches, download it
- **dig**: retrieve and store data according to bin
- **serve**: expose stored data using an API