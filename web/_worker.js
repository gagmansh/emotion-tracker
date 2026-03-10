export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/__/auth/")) {
      return proxyFirebaseAuth(request);
    }

    return env.ASSETS.fetch(request);
  },
};

async function proxyFirebaseAuth(request) {
  const requestUrl = new URL(request.url);
  const upstreamUrl = new URL(`https://emotiontracker-54eee.firebaseapp.com${requestUrl.pathname}${requestUrl.search}`);
  const headers = new Headers(request.headers);
  headers.set("host", upstreamUrl.host);

  const upstreamRequest = new Request(upstreamUrl, {
    method: request.method,
    headers,
    body: canHaveRequestBody(request.method) ? request.body : undefined,
    redirect: "manual",
  });

  const upstreamResponse = await fetch(upstreamRequest);
  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.set("cache-control", "no-store");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

function canHaveRequestBody(method) {
  return !["GET", "HEAD"].includes((method || "").toUpperCase());
}
