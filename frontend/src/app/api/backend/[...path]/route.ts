import { NextRequest, NextResponse } from 'next/server';

// The base URL of the API server
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const path = params.path.join('/');
    
    // Forward the request to the API server
    const response = await fetch(`${API_BASE_URL}/${path}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('API backend error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch data from API' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const path = params.path.join('/');
    
    // Get the request body
    const body = await request.json();

    // Forward the request to the API server
    const response = await fetch(`${API_BASE_URL}/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('API backend error:', error);
    return NextResponse.json(
      { error: 'Failed to post data to API' },
      { status: 500 }
    );
  }
} 