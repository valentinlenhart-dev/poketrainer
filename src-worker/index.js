/**
 * Cloudflare Worker — pokenom.fr
 * Sert les assets statiques et force charset=utf-8 sur toutes les réponses HTML.
 */
export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);

    const ct = response.headers.get('Content-Type') ?? '';

    // Ajouter charset=utf-8 si la réponse est du HTML et que le charset manque
    if (ct.includes('text/html') && !ct.toLowerCase().includes('charset')) {
      const headers = new Headers(response.headers);
      headers.set('Content-Type', 'text/html; charset=utf-8');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }

    return response;
  },
};
