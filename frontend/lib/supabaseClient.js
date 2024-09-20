import { createClient } from '@supabase/supabase-js'

let supabase = null;

if (typeof window !== 'undefined') {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  console.log('Supabase URL:', supabaseUrl);
  console.log('Supabase Anon Key:', supabaseAnonKey ? 'Set' : 'Not set');

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Supabase URL or Anon Key is missing');
  } else {
    supabase = createClient(supabaseUrl, supabaseAnonKey);
  }
} else {
  console.log('Supabase client not initialized (server-side)');
}

export { supabase };

// Only set up the channel if we're in a browser environment
let channel;
if (typeof window !== 'undefined' && supabase) {
  channel = supabase.channel('custom-all-channel');

  channel
    .on('presence', { event: 'sync' }, () => {
      console.log('Realtime connection synced');
    })
    .on('presence', { event: 'join' }, ({ key, newPresences }) => {
      console.log('New connection joined:', key, newPresences);
    })
    .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
      console.log('Connection left:', key, leftPresences);
    })
    .subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        console.log('Successfully subscribed to real-time channel');
      }
    });
}

export { channel as supabaseChannel };
