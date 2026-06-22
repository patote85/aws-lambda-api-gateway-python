# Versionamento de API + Deprecation
def get_api_version(event):
    return event.get('headers', {}).get('X-API-Version', 'v1')

# Exemplo de deprecation warning
if version == 'v1':
    logger.warning("API v1 está deprecated. Migre para v2.")