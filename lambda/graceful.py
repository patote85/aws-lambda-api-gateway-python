# Graceful Degradation + preparação para FIS
def process_with_fallback(item):
    try:
        # tenta operação normal
        return save_to_dynamodb(item)
    except Exception:
        # fallback: enfileira ou retorna mensagem amigável
        logger.warning("DynamoDB indisponível - usando fallback")
        return {"status": "queued", "message": "Solicitação será processada posteriormente"}