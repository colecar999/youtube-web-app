import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

console.log('Supabase URL:', supabaseUrl);
console.log('Supabase Anon Key:', supabaseAnonKey ? 'Set' : 'Not set');

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Remove these lines as they are not compatible with the current Supabase version
// supabase.realtime.onOpen(() => console.log('Realtime connection opened'));
// supabase.realtime.onClose(() => console.log('Realtime connection closed'));
// supabase.realtime.onError((error) => console.error('Realtime error:', error));

// Instead, you can use the following if you want to log connection status:
supabase.channel('system').on('system', { event: '*' }, (payload) => {
  console.log('Realtime event:', payload);
}).subscribe();
