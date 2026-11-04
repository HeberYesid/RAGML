<#
Local UI integration checks. Requires an already-running web server and agent-browser.
Controlled HTTP responses exercise rendering, not model quality or business validity.
#>
param([string]$BaseUrl = 'http://127.0.0.1:8006')

$ErrorActionPreference = 'Stop'
if ($BaseUrl -notmatch '^http://127\.0\.0\.1:\d+$') {
    throw 'These checks only target an explicit local loopback server.'
}
$previousSession = $env:AGENT_BROWSER_SESSION
$env:AGENT_BROWSER_SESSION = 'ragml-web-smoke-' + [guid]::NewGuid().ToString('N').Substring(0, 10)

function Invoke-Browser {
    & agent-browser @args
    if ($LASTEXITCODE -ne 0) { throw "Browser command failed: $($args[0])" }
}

function Assert-Page([string]$Script) {
    $Script | & agent-browser eval --stdin
    if ($LASTEXITCODE -ne 0) { throw 'Browser assertion failed.' }
}

try {
    $catalog = Invoke-RestMethod "$BaseUrl/v1/web/catalog"
    $variant = $catalog.variants[0]
    $fixture = @{
        schema_version = '0.1'
        request_id = '2f3a54c5-8aca-48af-bb5c-c97f833a8c63'
        session_id = '3da23ae5-6273-4cf1-8241-2f1546533df5'
        store_id = $catalog.profile.store_id
        data_mode = $catalog.profile.data_mode
        status = 'answered'
        answer = 'Respuesta controlada de interfaz. <img src=x onerror="window.__uiInjected=true">'
        claims = @(@{ text = 'Afirmación de prueba'; citation_ids = @('c1') })
        citations = @(@{
            kind = 'document'; citation_id = 'c1'; store_id = $catalog.profile.store_id
            source_id = 'ui-synthetic-policy'; source_version = '1'; chunk_id = 'ui-chunk'
            location = @{ page = 2; section = 'Condiciones de prueba'; paragraph = 3; table = 'A' }
            excerpt = 'Extracto controlado para verificar la presentación de las fuentes.'
        }, @{
            kind = 'commercial'; citation_id = 'c2'; store_id = $catalog.profile.store_id
            source_id = 'ui-synthetic-price'; source_version = '1'; snapshot_id = 'snapshot-ui'
            variant_id = $variant.variant_id; field = 'price'
            source_updated_at = '2020-01-01T00:00:00Z'; expires_at = '2020-01-02T00:00:00Z'
        })
        products = @(@{ product_id = $variant.product_id; variant_id = $variant.variant_id })
        warnings = @('Respuesta controlada: comprobación de interfaz, sin inferencia del modelo.')
        versions = @{ catalog_profile = $catalog.profile.revision; corpus = 'ui-fixture-1' }
    }
    Invoke-Browser open $BaseUrl
    Invoke-Browser set viewport 1440 1000
    Invoke-Browser wait --fn 'document.querySelectorAll(".category").length > 0'
    Assert-Page @'
if (!document.querySelector('#chat-form')) throw new Error('Missing form');
if (document.querySelector('#data-mode').textContent === 'Datos sin verificar') throw new Error('Unknown data mode');
if (document.documentElement.scrollWidth > innerWidth) throw new Error('Desktop overflow');
'@
    Invoke-Browser network route '**/v1/chat' --body ($fixture | ConvertTo-Json -Compress -Depth 20)
    Invoke-Browser fill '#message' 'Consulta controlada'
    Invoke-Browser press Enter
    Invoke-Browser wait --text 'Respuesta controlada de interfaz.'
    Invoke-Browser find role link click --name 'Ver fuente 1 de la afirmación: Afirmación de prueba'
    Assert-Page @'
const source = document.querySelector('.sources');
if (!source.open || !source.textContent.includes('Página 2') || !source.textContent.includes('Párrafo 3') || !source.textContent.includes('Tabla: A')) throw new Error('Source details missing');
if (!source.textContent.includes('Dato vencido')) throw new Error('Expired commercial citation not labeled');
if (document.querySelectorAll('.product-card').length !== 1) throw new Error('Product reference missing');
if (window.__uiInjected || document.querySelector('.turn img')) throw new Error('Unsafe HTML rendering');
if (document.querySelector('#message').value !== '') throw new Error('Successful draft not cleared');
'@
    foreach ($status in @('clarification_required', 'insufficient_evidence', 'temporarily_unavailable')) {
        $fixture.status = $status
        $fixture.answer = "Controlled status: $status"
        $fixture.claims = @()
        $fixture.citations = @()
        $fixture.products = @()
        Invoke-Browser network unroute '**/v1/chat'
        Invoke-Browser network route '**/v1/chat' --body ($fixture | ConvertTo-Json -Compress -Depth 20)
        Invoke-Browser fill '#message' 'Otra consulta controlada'
        Invoke-Browser click '#send'
        Invoke-Browser wait --text $fixture.answer
    }
    Invoke-Browser click '#new-session'
    Assert-Page @'
if (document.querySelector('#transcript').children.length || document.querySelector('#welcome').hidden) throw new Error('New conversation did not clear the view');
if (document.activeElement.id !== 'message') throw new Error('Focus was not returned to input');
const input = document.querySelector('#message');
input.value = 'Texto en composición';
input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true, bubbles: true, cancelable: true }));
if (!document.querySelector('#pending').hidden) throw new Error('IME committed a request');
'@
    Invoke-Browser network unroute '**/v1/chat'
    Invoke-Browser network route '**/v1/chat' --abort
    Invoke-Browser fill '#message' 'Texto que debe conservarse'
    Invoke-Browser click '#send'
    Invoke-Browser wait --text 'No se pudo conectar con el servicio local.'
    Assert-Page @'
if (document.querySelector('#message').value !== 'Texto que debe conservarse') throw new Error('Draft lost on failure');
if (document.querySelector('#retry').hidden) throw new Error('Retry missing');
if (document.querySelector('#send').disabled) throw new Error('Send remained disabled');
'@
    Invoke-Browser network unroute '**/v1/chat'
    Invoke-Browser click '#new-session'
    foreach ($width in @(390, 320)) {
        Invoke-Browser set viewport $width 844
        Assert-Page @'
if (document.documentElement.scrollWidth > innerWidth) throw new Error('Mobile overflow');
if (getComputedStyle(document.querySelector('#send')).display === 'none') throw new Error('Send missing on mobile');
'@
    }
    Invoke-Browser set viewport 390 844
    Invoke-Browser find role button click --name 'Revisa las políticas Cambios, garantías y condiciones'
    Assert-Page @'
if (!document.querySelector('#message').value.includes('garantías')) throw new Error('Starter did not prepare a draft');
if (document.activeElement.id !== 'message') throw new Error('Starter did not focus the draft');
'@
    Invoke-Browser press Tab
    Assert-Page 'if (document.activeElement.id !== "send") throw new Error("Keyboard cannot reach send");'
    Write-Output 'PASS: sources, product references, four response states, safe text rendering, new session, IME, network failure, draft recovery, mobile reflow, starters and keyboard.'
}
finally {
    & agent-browser close
    $env:AGENT_BROWSER_SESSION = $previousSession
}
