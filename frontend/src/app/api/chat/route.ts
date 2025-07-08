import { NextResponse } from 'next/server';

// The backend API is running on port 8000
const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  try {
    const { query } = await request.json();

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    const fastapiResponse = await fetch(`${FASTAPI_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!fastapiResponse.ok) {
      const errorBody = await fastapiResponse.text();
      console.error('FastAPI error:', errorBody);
      return NextResponse.json(
        { error: `Error from backend: ${fastapiResponse.statusText}`, details: errorBody },
        { status: fastapiResponse.status }
      );
    }

    const data = await fastapiResponse.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in chat API route:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json({ error: 'Internal Server Error', details: errorMessage }, { status: 500 });
  }
}
