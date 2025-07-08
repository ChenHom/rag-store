import { NextResponse } from 'next/server';

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // We need to forward the form data to the backend
    const backendFormData = new FormData();
    backendFormData.append('file', file);

    const fastapiResponse = await fetch(FASTAPI_URL, {
      method: 'POST',
      body: backendFormData,
      // Let the browser set the Content-Type header with the correct boundary
    });

    const data = await fastapiResponse.json();

    if (!fastapiResponse.ok) {
      console.error('FastAPI upload error:', data);
      return NextResponse.json(
        { error: `Error from backend: ${fastapiResponse.statusText}`, details: data.detail },
        { status: fastapiResponse.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in upload API route:', error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json({ error: 'Internal Server Error', details: errorMessage }, { status: 500 });
  }
}
