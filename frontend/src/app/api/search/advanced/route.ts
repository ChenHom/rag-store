import { NextResponse } from 'next/server';

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost';

export async function POST(request: Request) {
  try {
    const searchParams = await request.json();

    const fastapiResponse = await fetch(`${FASTAPI_URL}/api/search/advanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchParams),
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
    console.error('Error in advanced search API route:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json(
      { error: 'Internal server error', details: errorMessage },
      { status: 500 }
    );
  }
}
