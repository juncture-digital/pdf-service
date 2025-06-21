
# Web-to-PDF Converter Service

A high-performance web page to PDF conversion service built with FastAPI and Playwright, designed to work seamlessly with the Juncture platform and optimized for deployment on Google Cloud Run.

## 🚀 Features

- **High-Quality PDF Generation**: Uses Playwright's Chromium engine for accurate rendering
- **Flexible Formatting**: Supports custom page sizes, margins, orientation, and scaling
- **Element Control**: Hide specific elements, classes, IDs, or tags from the PDF output
- **Page Break Management**: Control page breaks before/after elements or keep elements together
- **Custom Styling**: Inject custom CSS for print-specific styling
- **Image Optimization**: Wait for images and dynamic content to load before conversion
- **Rate Limiting**: Built-in protection against abuse
- **Health Monitoring**: Comprehensive health check endpoint
- **Element Inspection**: Built-in tool to inspect page elements for better customization

## 🏗️ Architecture

The service is containerized using Docker and designed for serverless deployment on Google Cloud Run. It uses:

- **FastAPI**: Modern, fast web framework for building APIs
- **Playwright**: Browser automation library for high-fidelity web page rendering
- **Chromium**: Headless browser engine for PDF generation
- **Google Cloud Run**: Serverless container platform with auto-scaling

## 📦 Quick Start

### Prerequisites

- Docker
- Google Cloud SDK (for deployment)
- Python 3.11+ (for local development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo>
   cd pdf-service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Run the service**
   ```bash
   uvicorn pdf_service_gcr:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Test the service**
   ```bash
   curl "http://localhost:8080/health"
   curl "http://localhost:8080/pdf?url=https://example.com" --output test.pdf
   ```

### Docker Development

1. **Build the Docker image**
   ```bash
   docker build -t pdf-converter .
   ```

2. **Run the container**
   ```bash
   docker run -p 8080:8080 pdf-converter
   ```

## 🌐 Google Cloud Run Deployment

### Automated Deployment

Use the provided deployment script for easy setup:

```bash
chmod +x deploy-gcr.sh
./deploy-gcr.sh
```

The script will:
- Enable required Google Cloud APIs
- Create an Artifact Registry repository
- Build and push the Docker image
- Deploy to Cloud Run with optimized settings
- Provide the service URL and usage examples

### Manual Deployment

1. **Set up your Google Cloud project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

2. **Create Artifact Registry repository**
   ```bash
   gcloud artifacts repositories create pdf-converter-repo \
     --repository-format=docker \
     --location=us-central1
   ```

3. **Build and deploy**
   ```bash
   gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/pdf-converter-repo/pdf-converter
   
   gcloud run deploy pdf-converter \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/pdf-converter-repo/pdf-converter \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2 \
     --timeout 1800 \
     --concurrency 10 \
     --max-instances 10
   ```

## 📖 API Documentation

### Endpoints

#### `GET /`
Redirects to the interactive API documentation.

#### `GET /health`
Health check endpoint that returns service status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-20T10:30:00",
  "environment": "Google Cloud Run",
  "engine": "Playwright",
  "browser_path": "/path/to/chromium",
  "python_version": "3.11.0"
}
```

#### `GET /pdf`
Convert a web page to PDF with extensive customization options.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | **required** | The URL to convert to PDF |
| `format` | string | "Letter" | Page format (Letter, A4, Legal, etc.) |
| `width` | string | - | Custom page width (overrides format) |
| `height` | string | - | Custom page height (overrides format) |
| `landscape` | boolean | false | Page orientation |
| `scale` | float | 0.9 | Scaling factor (0.1-2.0) |
| `marginTop` | string | "0.75in" | Top margin |
| `marginBottom` | string | "0.5in" | Bottom margin |
| `marginLeft` | string | "0.2in" | Left margin |
| `marginRight` | string | "0.2in" | Right margin |
| `printBackground` | boolean | true | Include background graphics |
| `displayHeaderFooter` | boolean | true | Show header and footer |
| `pageRanges` | string | "" | Specific page ranges to print |
| `timeout` | integer | 30000 | Page load timeout (ms) |
| `waitTime` | integer | 2000 | Additional wait time (ms) |
| `waitForImages` | boolean | true | Wait for images to load |
| `viewportWidth` | integer | 1280 | Viewport width |
| `viewportHeight` | integer | 720 | Viewport height |
| `deviceScaleFactor` | float | 1.0 | Device pixel ratio |
| `hideElements` | string | - | CSS selectors to hide |
| `hideClasses` | string | - | CSS classes to hide |
| `hideIds` | string | - | Element IDs to hide |
| `hideTags` | string | - | HTML tags to hide |
| `pageBreakBefore` | string | - | Add page breaks before elements |
| `pageBreakAfter` | string | - | Add page breaks after elements |
| `keepTogether` | string | - | Keep elements together |
| `customCSS` | string | - | Custom CSS to inject |

#### `GET /inspect`
Inspect a web page to identify elements for customization.

**Parameters:**
- `url` (required): The URL to inspect
- `timeout` (optional): Page load timeout

**Response:**
```json
{
  "url": "https://example.com",
  "elements_found": {
    "navigation": [...],
    "headers": [...],
    "footers": [...],
    "all_ids": [...],
    "common_classes": [...]
  },
  "hide_examples": {
    "by_tag": "hideTags=nav,footer,button",
    "by_class": "hideClasses=sidebar,advertisement",
    "by_id": "hideIds=header,navigation",
    "by_selector": "hideElements=.sidebar,.ad"
  }
}
```

## 🔧 Usage Examples

### Basic PDF Generation
```bash
curl "https://your-service-url/pdf?url=https://example.com" -o example.pdf
```

### Custom Page Size and Orientation
```bash
curl "https://your-service-url/pdf?url=https://example.com&format=A4&landscape=true" -o landscape.pdf
```

### Hide Navigation and Footer
```bash
curl "https://your-service-url/pdf?url=https://example.com&hideElements=nav,footer" -o clean.pdf
```

### Custom Viewport and Scaling
```bash
curl "https://your-service-url/pdf?url=https://example.com&viewportWidth=1920&scale=0.8" -o scaled.pdf
```

### Page Break Control
```bash
curl "https://your-service-url/pdf?url=https://example.com&pageBreakBefore=h1&keepTogether=.article" -o formatted.pdf
```

### Custom CSS Styling
```bash
curl "https://your-service-url/pdf?url=https://example.com&customCSS=body{font-size:14pt;}" -o styled.pdf
```

### Inspect Page Elements
```bash
curl "https://your-service-url/inspect?url=https://example.com" | jq
```

## 🎯 Juncture Integration

This service is specifically designed to work with [Juncture](https://juncture-digital.org/), a platform for creating interactive web pages from Markdown. Common Juncture-specific usage patterns:

### Hide Juncture UI Elements
```bash
curl "https://your-service-url/pdf?url=https://your-juncture-essay.com&hideClasses=juncture-header,juncture-footer,toolbar" -o essay.pdf
```

### Optimize for Academic Papers
```bash
curl "https://your-service-url/pdf?url=https://your-juncture-essay.com&format=A4&marginTop=1in&marginBottom=1in&pageBreakBefore=h1,h2&keepTogether=.citation" -o academic.pdf
```

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 8080 |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | - |
| `PYTHONUNBUFFERED` | Python output buffering | 1 |
| `PLAYWRIGHT_BROWSERS_PATH` | Browser installation path | - |

### Rate Limiting

The service implements basic rate limiting:
- **Limit**: 60 requests per minute per IP
- **Response**: HTTP 429 when exceeded
- **Storage**: In-memory (resets on restart)

### Resource Limits

**Cloud Run Configuration:**
- **Memory**: 4GB
- **CPU**: 2 vCPU
- **Timeout**: 30 minutes
- **Concurrency**: 10 requests
- **Max Instances**: 10

**Parameter Limits:**
- Timeout: 5-120 seconds
- Viewport: 320x240 to 4000x4000 pixels
- Scale: 0.1 to 2.0
- Wait time: 0-30 seconds

## 🐛 Troubleshooting

### Common Issues

**PDF Generation Fails**
- Check if the URL is accessible
- Verify timeout settings for slow-loading pages
- Ensure the page doesn't require authentication

**Empty or Corrupted PDFs**
- Increase `waitTime` for dynamic content
- Enable `waitForImages` for image-heavy pages
- Check for JavaScript errors on the page

**Timeout Errors**
- Increase the `timeout` parameter
- Optimize the target page's loading speed
- Consider breaking large pages into sections

**Rate Limit Errors**
- Implement client-side rate limiting
- Contact the service administrator for higher limits
- Consider caching results for repeated requests

### Debugging

**Check Service Health**
```bash
curl "https://your-service-url/health"
```

**Inspect Page Elements**
```bash
curl "https://your-service-url/inspect?url=YOUR_URL"
```

**Monitor Logs**
```bash
gcloud run services logs tail pdf-converter --region us-central1
```

## 💰 Cost Estimation

### Google Cloud Run Pricing

**Free Tier:**
- 2 million requests/month
- 400,000 GB-seconds of memory
- 200,000 vCPU-seconds

**Beyond Free Tier:**
- **Requests**: $0.40 per million requests
- **Memory**: $0.0000025 per GB-second
- **CPU**: $0.000024 per vCPU-second

**Example Monthly Costs:**
- 10K requests: Free
- 100K requests: Free
- 1M requests: Free
- 5M requests: ~$1.20
- 10M requests: ~$3.20

## 🔒 Security

### Built-in Protections

- **Rate Limiting**: Prevents abuse
- **URL Validation**: Blocks invalid URLs
- **Sandboxed Execution**: Containers run in isolated environments
- **No Authentication Required**: Public service (configure as needed)

### Security Considerations

- **HTTPS Only**: Use HTTPS for production deployments
- **Access Control**: Implement authentication if needed
- **Network Policies**: Restrict access using Cloud Run IAM
- **Monitoring**: Set up alerting for unusual usage patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for API changes
- Test with various web pages and browsers

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for excellent browser automation
- [FastAPI](https://fastapi.tiangolo.com/) for the modern web framework
- [Google Cloud Run](https://cloud.google.com/run) for serverless deployment
- [Juncture](https://juncture-digital.org/) for the inspiration and use case

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/web-to-pdf-converter/issues)
- **Documentation**: [API Docs](https://your-service-url/docs)
- **Community**: [Discussions](https://github.com/your-username/web-to-pdf-converter/discussions)

---

**Built with ❤️ for the Juncture community**