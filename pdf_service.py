import logging
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from hashlib import sha256
from urllib.parse import urlparse
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.responses import RedirectResponse
from typing import Optional
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web to PDF Converter",
    description="Web page to PDF conversion using Playwright on Google Cloud Run",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Simple in-memory rate limiting
rate_limit_storage = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60

def is_valid_url(url: str) -> bool:
    """Validate URL format and scheme"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

def is_rate_limited(client_ip: str) -> bool:
    """Simple rate limiting check"""
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip] 
        if timestamp > minute_ago
    ]
    
    if len(rate_limit_storage[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        return True
    
    rate_limit_storage[client_ip].append(now)
    return False

@app.get('/')
async def root():
    return RedirectResponse(url='/docs')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Playwright availability
        async with async_playwright() as p:
            browsers = p.chromium
            browser_executable = browsers.executable_path
            
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "environment": "Google Cloud Run",
            "engine": "Playwright",
            "browser_path": str(browser_executable),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/pdf")
async def pdf(
    request: Request,
    url: str,
    displayHeaderFooter: Optional[bool] = True,
    landscape: Optional[bool] = False,
    marginBottom: Optional[str] = "0.5in",
    marginLeft: Optional[str] = "0.2in", 
    marginRight: Optional[str] = "0.2in",
    marginTop: Optional[str] = "0.75in",
    pageRanges: Optional[str] = '',
    format: Optional[str] = "Letter",  # A4, Letter, Legal, etc.
    width: Optional[str] = None,  # PDF page width (e.g., "8.5in", "210mm")
    height: Optional[str] = None,  # PDF page height (e.g., "11in", "297mm")
    printBackground: Optional[bool] = True,
    scale: Optional[float] = 0.9,
    timeout: Optional[int] = 180000,  # Playwright uses milliseconds
    waitForImages: Optional[bool] = True,  # Wait for images to load
    waitForIframes: Optional[bool] = True,  # Wait for iframes to load
    waitTime: Optional[int] = 2000,  # Additional wait time in milliseconds
    enableJavaScript: Optional[bool] = True,  # Enable/disable JavaScript
    viewportWidth: Optional[int] = 1280,  # Page width for rendering
    viewportHeight: Optional[int] = 720,  # Page height for rendering
    deviceScaleFactor: Optional[float] = 1.0,  # Device pixel ratio
    preferCSSPageSize: Optional[bool] = False,  # Use CSS @page size
    hideElements: Optional[str] = None,  # CSS selectors to hide (comma-separated)
    hideClasses: Optional[str] = None,  # Class names to hide (comma-separated)
    hideIds: Optional[str] = None,  # IDs to hide (comma-separated)
    hideTags: Optional[str] = None,  # HTML tags to hide (comma-separated)
    pageBreakBefore: Optional[str] = None,  # CSS selectors to force page break before
    pageBreakAfter: Optional[str] = None,  # CSS selectors to force page break after
    keepTogether: Optional[str] = None,  # CSS selectors to avoid breaking inside
    customCSS: Optional[str] = None):  # Custom CSS to inject
    
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Rate limiting check
    if is_rate_limited(client_ip):
        logger.warning(f'Rate limit exceeded for IP: {client_ip}')
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Validate URL
    if not is_valid_url(url):
        logger.warning(f'Invalid URL provided: {url}')
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    # Validate parameters
    if timeout < 5000 or timeout > 180000:
        raise HTTPException(status_code=400, detail="Timeout must be between 5000 and 180000 milliseconds")
    
    if waitTime < 0 or waitTime > 30000:
        raise HTTPException(status_code=400, detail="Wait time must be between 0 and 30000 milliseconds")
    
    if scale < 0.1 or scale > 2.0:
        raise HTTPException(status_code=400, detail="Scale must be between 0.1 and 2.0")
    
    if viewportWidth < 320 or viewportWidth > 4000:
        raise HTTPException(status_code=400, detail="Viewport width must be between 320 and 4000 pixels")
    
    if viewportHeight < 240 or viewportHeight > 4000:
        raise HTTPException(status_code=400, detail="Viewport height must be between 240 and 4000 pixels")
    
    logger.info(f'PDF conversion requested for URL: {url} from IP: {client_ip}')
    
    # Generate unique filename
    url_hash = sha256(url.encode('utf-8')).hexdigest()
    pdf_path = os.path.join(tempfile.gettempdir(), f'pdf_{url_hash}_{int(time.time())}.pdf')

    try:
        async with async_playwright() as p:
            # Launch browser with specific args for PDF generation
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    f'--window-size={viewportWidth},{viewportHeight}'
                ]
            )
            
            try:
                # Create page with specific viewport
                page = await browser.new_page(viewport={
                    'width': viewportWidth,
                    'height': viewportHeight,
                    'device_scale_factor': deviceScaleFactor
                })
                
                # Emulate print media and set extra HTTP headers
                await page.emulate_media(media='print')
                await page.set_extra_http_headers({
                    'User-Agent': f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PDF-Generator Viewport-{viewportWidth}x{viewportHeight}'
                })
                
                # Configure JavaScript if needed
                if not enableJavaScript:
                    await page.set_javascript_enabled(False)
                
                # Set longer timeout for slow-loading pages
                page.set_default_timeout(timeout)
                
                # Navigate to URL with timeout and wait for content to load
                await page.goto(url, timeout=timeout, wait_until='networkidle')
                
                # Build CSS rules
                css_rules = []
                
                # Width control
                css_rules.extend([
                    f'''body {{
                        width: {viewportWidth}px !important;
                        max-width: {viewportWidth}px !important;
                        min-width: {viewportWidth}px !important;
                    }}''',
                    f'''.container, .main, #main, #content, .content {{
                        width: {viewportWidth}px !important;
                        max-width: {viewportWidth}px !important;
                    }}'''
                ])
                
                # Hide elements
                if hideElements:
                    selectors = [s.strip() for s in hideElements.split(',') if s.strip()]
                    for selector in selectors:
                        css_rules.append(f'{selector} {{ display: none !important; }}')
                
                if hideClasses:
                    classes = [c.strip().lstrip('.') for c in hideClasses.split(',') if c.strip()]
                    for class_name in classes:
                        css_rules.append(f'.{class_name} {{ display: none !important; }}')
                
                if hideIds:
                    ids = [i.strip().lstrip('#') for i in hideIds.split(',') if i.strip()]
                    for id_name in ids:
                        css_rules.append(f'#{id_name} {{ display: none !important; }}')
                
                if hideTags:
                    tags = [t.strip() for t in hideTags.split(',') if t.strip()]
                    for tag in tags:
                        css_rules.append(f'{tag} {{ display: none !important; }}')
                
                # Page break controls
                if pageBreakBefore:
                    selectors = [s.strip() for s in pageBreakBefore.split(',') if s.strip()]
                    for selector in selectors:
                        css_rules.append(f'{selector} {{ break-before: page !important; page-break-before: always !important; }}')
                
                if pageBreakAfter:
                    selectors = [s.strip() for s in pageBreakAfter.split(',') if s.strip()]
                    for selector in selectors:
                        css_rules.append(f'{selector} {{ break-after: page !important; page-break-after: always !important; }}')
                
                if keepTogether:
                    selectors = [s.strip() for s in keepTogether.split(',') if s.strip()]
                    for selector in selectors:
                        css_rules.append(f'{selector} {{ break-inside: avoid !important; page-break-inside: avoid !important; }}')
                
                # Custom CSS
                if customCSS:
                    css_rules.append(customCSS)
                
                # Build complete CSS with print media queries
                css_content = f'''
                    @media print {{
                        {chr(10).join(css_rules)}
                        
                        /* Good defaults for print */
                        * {{
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                        }}
                        
                        /* Better typography for print */
                        body {{
                            font-size: 12pt;
                            line-height: 1.4;
                        }}
                        
                        h1, h2, h3, h4, h5, h6 {{
                            break-after: avoid !important;
                            page-break-after: avoid !important;
                        }}
                        
                        p, li {{
                            orphans: 3;
                            widows: 3;
                        }}
                        
                        img {{
                            max-width: 100% !important;
                            break-inside: avoid !important;
                            page-break-inside: avoid !important;
                        }}
                        
                        table {{
                            break-inside: avoid !important;
                            page-break-inside: avoid !important;
                        }}
                        
                        pre, blockquote {{
                            break-inside: avoid !important;
                            page-break-inside: avoid !important;
                        }}
                    }}
                    
                    /* Apply rules to screen view too */
                    {chr(10).join(css_rules)}
                '''
                
                if css_rules:
                    await page.add_style_tag(content=css_content)
                    logger.info(f'Applied {len(css_rules)} CSS rules including page break controls')
                
                # Additional waiting strategies for dynamic content
                if waitForImages or waitForIframes or waitTime > 0:
                    try:
                        # Wait for the page to be fully loaded
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        
                        if waitForImages:
                            # Wait for images to load
                            images = await page.query_selector_all('img')
                            if images:
                                logger.info(f'Found {len(images)} images, waiting for them to load...')
                                
                                # Scroll through the page to trigger lazy loading
                                await page.evaluate('''
                                    () => {
                                        return new Promise(resolve => {
                                            let totalHeight = 0;
                                            const distance = 100;
                                            const timer = setInterval(() => {
                                                const scrollHeight = document.body.scrollHeight;
                                                window.scrollBy(0, distance);
                                                totalHeight += distance;
                                                
                                                if(totalHeight >= scrollHeight){
                                                    clearInterval(timer);
                                                    resolve();
                                                }
                                            }, 100);
                                        });
                                    }
                                ''')
                                
                                # Wait for images to load
                                await page.evaluate('''
                                    async () => {
                                        const images = Array.from(document.querySelectorAll('img'));
                                        const imagePromises = images.map(img => {
                                            if (img.complete && img.naturalHeight !== 0) {
                                                return Promise.resolve();
                                            }
                                            return new Promise(resolve => {
                                                img.onload = () => resolve();
                                                img.onerror = () => resolve(); // Resolve even on error to not block
                                                // Set a timeout to avoid hanging
                                                setTimeout(() => resolve(), 5000);
                                            });
                                        });
                                        await Promise.all(imagePromises);
                                    }
                                ''')
                                
                                # Scroll back to top
                                await page.evaluate('window.scrollTo(0, 0)')
                                await page.wait_for_timeout(500)
                        
                        if waitForIframes:
                            # Wait for images to load
                            iframes = await page.query_selector_all('iframe')
                            if iframes:
                                logger.info(f'Found {len(iframes)} iframes, waiting for them to load...')
                                
                                # Scroll through the page to trigger lazy loading
                                await page.evaluate('''
                                    () => {
                                        return new Promise(resolve => {
                                            let totalHeight = 0;
                                            const distance = 100;
                                            const timer = setInterval(() => {
                                                const scrollHeight = document.body.scrollHeight;
                                                window.scrollBy(0, distance);
                                                totalHeight += distance;
                                                
                                                if(totalHeight >= scrollHeight){
                                                    clearInterval(timer);
                                                    resolve();
                                                }
                                            }, 100);
                                        });
                                    }
                                ''')
                                
                                # Wait for iframes to load
                                await page.evaluate('''
                                    async () => {
                                        const iframes = Array.from(document.querySelectorAll('iframe'));
                                        const iframePromises = iframes.map(iframe => {
                                            if (iframe.complete && iframe.naturalHeight !== 0) {
                                                return Promise.resolve();
                                            }
                                            return new Promise(resolve => {
                                                iframe.onload = () => resolve();
                                                iframe.onerror = () => resolve(); // Resolve even on error to not block
                                                // Set a timeout to avoid hanging
                                                setTimeout(() => resolve(), 5000);
                                            });
                                        });
                                        await Promise.all(iframePromises);
                                    }
                                ''')
                                
                                # Scroll back to top
                                await page.evaluate('window.scrollTo(0, 0)')
                                await page.wait_for_timeout(500)
                                
                        # Additional wait time for other dynamic content
                        if waitTime > 0:
                            logger.info(f'Waiting additional {waitTime}ms for dynamic content...')
                            await page.wait_for_timeout(waitTime)
                        
                        # Wait for any ongoing network requests to complete
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        
                    except Exception as wait_error:
                        logger.warning(f'Some dynamic content may not have loaded completely: {wait_error}')
                
                # Generate PDF with proper options
                pdf_options = {
                    'path': pdf_path,
                    'landscape': landscape,
                    'print_background': printBackground,
                    'scale': scale,
                    'display_header_footer': displayHeaderFooter,
                    'prefer_css_page_size': preferCSSPageSize,
                    'margin': {
                        'top': marginTop,
                        'bottom': marginBottom,
                        'left': marginLeft,
                        'right': marginRight,
                    }
                }
                
                # Set page size - either format or custom width/height
                if width and height:
                    pdf_options['width'] = width
                    pdf_options['height'] = height
                    logger.info(f'Using custom page size: {width} x {height}')
                else:
                    pdf_options['format'] = format
                    logger.info(f'Using standard format: {format}')
                
                if pageRanges:
                    pdf_options['page_ranges'] = pageRanges
                
                if displayHeaderFooter:
                    pdf_options['header_template'] = '<span class="title"></span>'
                    pdf_options['footer_template'] = '<span class="pageNumber"></span> of <span class="totalPages"></span>'
                
                logger.info(f'Generating PDF with viewport {viewportWidth}x{viewportHeight}, scale {scale}')
                await page.pdf(**pdf_options)
                
            finally:
                await browser.close()
        
        # Check if file was created successfully
        if not os.path.exists(pdf_path):
            logger.error(f'PDF file was not created: {pdf_path}')
            raise HTTPException(status_code=500, detail="PDF generation failed")
        
        # Read PDF file safely
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
        except IOError as e:
            logger.error(f'Failed to read PDF file: {e}')
            raise HTTPException(status_code=500, detail="Failed to read generated PDF")
        
        # Check if PDF has content
        if len(pdf_content) == 0:
            logger.error('Generated PDF file is empty')
            raise HTTPException(status_code=500, detail="Generated PDF is empty")
        
        logger.info(f'PDF generated successfully: {len(pdf_content)} bytes')
                
        parsed_url = urlparse(url)
        path_segments = [seg for seg in parsed_url.path.split('/') if seg]
        filename = f"{path_segments[-1]}.pdf" if path_segments else "document.pdf"

        return Response(
            status_code=200,
            media_type='application/pdf',
            content=pdf_content,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            }
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f'PDF conversion failed for URL {url}: {error_msg}')
        
        if "TimeoutError" in str(type(e)) or "timeout" in error_msg.lower():
            raise HTTPException(status_code=408, detail="PDF generation timed out")
        elif "net::" in error_msg or "ERR_" in error_msg:
            raise HTTPException(status_code=502, detail="Unable to access the provided URL")
        else:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {error_msg}")
    
    finally:
        # Clean up
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except OSError as e:
            logger.warning(f'Failed to clean up temporary file {pdf_path}: {e}')
