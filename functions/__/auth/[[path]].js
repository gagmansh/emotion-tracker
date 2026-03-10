export async function onRequest(context) {
  const requestUrl = new URL(context.request.url);
  const pathValue = context.params.path;
  const pathSegments = Array.isArray(pathValue)
    ? pathValue
    : typeof pathValue === "string" && pathValue.length > 0
      ? [pathValue]
      : [];

  const upstreamUrl = new URL("https://emotiontracker-54eee.firebaseapp.com/__/auth/");
  upstreamUrl.pathname += pathSegments.join("/");
  upstreamUrl.search = requestUrl.search;

  const headers = new Headers(context.request.headers);
  headers.set("host", upstreamUrl.host);

  const upstreamResponse = await fetch(upstreamUrl, {
    method: context.request.method,
    headers,
    body: canHaveRequestBody(context.request.method) ? context.request.body : undefined,
    redirect: "manual",
  });

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
