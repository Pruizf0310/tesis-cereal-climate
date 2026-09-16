import {NextResponse} from 'next/server';
export {GET} from '../hazard-probability/route';
export async function POST(){return NextResponse.json({ok:false,message:'The latitude-band calculator has been retired. Reload the calculator to use coordinate-specific consecutive intervals and the audited hazard-probability API.'},{status:410});}
