"""CLI interface for PDF2AlloyDB client."""
import argparse
import json
import sys
from uuid import UUID
from typing import Optional

from client.api_client import PDF2AlloyDBClient


def print_json(data, indent=2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


def process_document_cmd(args, client: PDF2AlloyDBClient):
    """Process a document command."""
    try:
        result = client.process_document(
            file_id=args.file_id,
            filename=args.filename
        )
        print("Document processed successfully:")
        print_json(result)
    except Exception as e:
        print(f"Error processing document: {e}", file=sys.stderr)
        sys.exit(1)


def batch_process_cmd(args, client: PDF2AlloyDBClient):
    """Batch process documents command."""
    try:
        result = client.batch_process_documents(
            file_ids=args.file_ids,
            filenames=args.filenames
        )
        print(f"Batch processing completed:")
        print(f"  Processed: {result['processed']} documents")
        if result.get('errors'):
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"    - {error['filename']}: {error['error']}")
        print_json(result)
    except Exception as e:
        print(f"Error in batch processing: {e}", file=sys.stderr)
        sys.exit(1)


def list_documents_cmd(args, client: PDF2AlloyDBClient):
    """List documents command."""
    try:
        documents = client.list_documents(limit=args.limit, offset=args.offset)
        print(f"Found {len(documents)} documents:")
        print_json(documents)
    except Exception as e:
        print(f"Error listing documents: {e}", file=sys.stderr)
        sys.exit(1)


def get_document_cmd(args, client: PDF2AlloyDBClient):
    """Get document command."""
    try:
        doc_id = UUID(args.doc_id)
        document = client.get_document(doc_id)
        print_json(document)
    except ValueError:
        print(f"Invalid UUID: {args.doc_id}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error getting document: {e}", file=sys.stderr)
        sys.exit(1)


def search_cmd(args, client: PDF2AlloyDBClient):
    """Search command."""
    try:
        results = client.search_documents(
            query=args.query,
            limit=args.limit,
            search_type=args.type
        )
        print(f"Found {len(results)} results:")
        print_json(results)
    except Exception as e:
        print(f"Error searching: {e}", file=sys.stderr)
        sys.exit(1)


def list_drive_files_cmd(args, client: PDF2AlloyDBClient):
    """List Drive files command."""
    try:
        result = client.list_drive_files()
        print(f"Found {result['count']} PDF files in Google Drive:")
        print_json(result)
    except Exception as e:
        print(f"Error listing Drive files: {e}", file=sys.stderr)
        sys.exit(1)


def delete_document_cmd(args, client: PDF2AlloyDBClient):
    """Delete document command."""
    try:
        doc_id = UUID(args.doc_id)
        client.delete_document(doc_id)
        print(f"Document {doc_id} deleted successfully")
    except ValueError:
        print(f"Invalid UUID: {args.doc_id}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error deleting document: {e}", file=sys.stderr)
        sys.exit(1)


def health_check_cmd(args, client: PDF2AlloyDBClient):
    """Health check command."""
    try:
        result = client.health_check()
        print_json(result)
        if result.get('database') == 'disconnected':
            print("\n⚠️  Database is disconnected. Consider running 'reconnect-db' command.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


def reconnect_db_cmd(args, client: PDF2AlloyDBClient):
    """Reconnect database command."""
    try:
        print("Reconnecting to AlloyDB database...")
        result = client.reconnect_database()
        print_json(result)
        if result.get('connection_healthy'):
            print("\n✅ Database reconnected successfully!")
        else:
            print("\n⚠️  Database reconnected but connection test failed.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error reconnecting database: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PDF2AlloyDB CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='Base URL of the API server (default: http://localhost:8000)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process document command
    process_parser = subparsers.add_parser('process', help='Process a PDF document')
    process_group = process_parser.add_mutually_exclusive_group(required=True)
    process_group.add_argument('--file-id', help='Google Drive file ID')
    process_group.add_argument('--filename', help='Filename to process')
    
    # Batch process command
    batch_parser = subparsers.add_parser('batch-process', help='Process multiple PDF documents. If no file-ids or filenames provided, processes all PDFs in the folder.')
    batch_group = batch_parser.add_mutually_exclusive_group(required=False)
    batch_group.add_argument('--file-ids', nargs='+', help='List of Google Drive file IDs')
    batch_group.add_argument('--filenames', nargs='+', help='List of filenames to process')
    
    # List documents command
    list_parser = subparsers.add_parser('list', help='List all processed documents')
    list_parser.add_argument('--limit', type=int, default=100, help='Maximum number of documents')
    list_parser.add_argument('--offset', type=int, default=0, help='Number of documents to skip')
    
    # Get document command
    get_parser = subparsers.add_parser('get', help='Get a document with instructions')
    get_parser.add_argument('doc_id', help='Document UUID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Perform vector similarity search')
    search_parser.add_argument('query', help='Search query text')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    search_parser.add_argument(
        '--type',
        choices=['documents', 'instructions'],
        default='documents',
        help='Type of search'
    )
    
    # List Drive files command
    drive_parser = subparsers.add_parser('list-drive', help='List PDF files in Google Drive')
    
    # Delete document command
    delete_parser = subparsers.add_parser('delete', help='Delete a document')
    delete_parser.add_argument('doc_id', help='Document UUID')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check API health status')
    
    # Reconnect database command
    reconnect_parser = subparsers.add_parser('reconnect-db', help='Manually reconnect to AlloyDB database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    client = PDF2AlloyDBClient(base_url=args.base_url)
    
    # Route to appropriate command handler
    commands = {
        'process': process_document_cmd,
        'batch-process': batch_process_cmd,
        'list': list_documents_cmd,
        'get': get_document_cmd,
        'search': search_cmd,
        'list-drive': list_drive_files_cmd,
        'delete': delete_document_cmd,
        'health': health_check_cmd,
        'reconnect-db': reconnect_db_cmd
    }
    
    commands[args.command](args, client)


if __name__ == '__main__':
    main()

