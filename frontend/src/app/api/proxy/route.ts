import { NextRequest, NextResponse } from 'next/server';

// The base URL of the API server
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export async function GET(request: NextRequest) {
  try {
    // Get the endpoint from the URL query parameters
    const searchParams = request.nextUrl.searchParams;
    const endpoint = searchParams.get('endpoint');
    
    if (!endpoint) {
      return NextResponse.json(
        { error: 'Missing endpoint parameter' },
        { status: 400 }
      );
    }

    // Forward the request to the API server
    const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch data from API' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Get the endpoint from the URL query parameters
    const searchParams = request.nextUrl.searchParams;
    const endpoint = searchParams.get('endpoint');
    
    if (!endpoint) {
      return NextResponse.json(
        { error: 'Missing endpoint parameter' },
        { status: 400 }
      );
    }

    // Get the request body
    const body = await request.json();

    // Forward the request to the API server
    const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
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
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to post data to API' },
      { status: 500 }
    );
  }
} 