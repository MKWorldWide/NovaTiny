"""
NovaTiny Flask Application

This module serves as the main entry point for the NovaTiny web application,
integrating Divina-L3, WhispurrNet, and NovaSanctum.
"""
from flask import Flask, render_template, jsonify, request
import os
import json
from fusion_protocol import FusionProtocol, FusionConfig
import asyncio

app = Flask(__name__, static_folder='.', static_url_path='')

# Initialize Fusion Protocol
fusion_config = FusionConfig(
    codename="NovaTiny-Web",
    enable_quantum_sync=True,
    resonance_frequency=432.0
)
fusion = FusionProtocol(fusion_config)

# Ensure the event loop is properly set up for async operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/')
def index():
    """Serve the main index page."""
    return app.send_static_file('index.html')

@app.route('/api/status', methods=['GET'])
async def get_status():
    """Get the current system status."""
    try:
        status = await fusion.activate()
        return jsonify({
            'status': 'operational',
            'protocol': 'divina-l3',
            'version': '1.0.0',
            'fusion': status,
            'services': {
                'whispurr_net': status.get('whispurr_net', False),
                'nova_sanctum': status.get('nova_sanctum', False)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quantum/sync', methods=['POST'])
async def quantum_sync():
    """Handle quantum synchronization requests."""
    try:
        data = request.get_json()
        result = await fusion._divina_hooks.handle_whispurr_event({
            'type': 'quantum_sync_request',
            'id': data.get('id', 'unknown'),
            'timestamp': data.get('timestamp')
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sanctum/echo', methods=['POST'])
async def sanctum_echo():
    """Handle NovaSanctum echo requests."""
    try:
        data = request.get_json()
        result = await fusion._divina_hooks.handle_nova_sanctum_event({
            'type': 'sanctum_echo',
            'message': data.get('message', ''),
            'timestamp': data.get('timestamp')
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the app with Gunicorn if available, otherwise use Flask's dev server
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
