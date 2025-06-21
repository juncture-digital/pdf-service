#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse, uvicorn

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Web page to PDF converter using Playwright')
    parser.add_argument('--reload', type=bool, default=True, help='Reload on change')
    parser.add_argument('--port', type=int, default=8888, help='HTTP port')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    args = parser.parse_args()
    uvicorn.run('pdf_service:app', host=args.host, port=args.port, reload=args.reload)