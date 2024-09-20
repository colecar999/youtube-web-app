import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

console.log('Supabase URL:', supabaseUrl);
console.log('Supabase Anon Key:', supabaseAnonKey ? 'Set' : 'Not set');

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Supabase URL or Anon Key is missing');
  throw new Error('Supabase configuration is incomplete');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Set up real-time listeners using the new approach
const channel = supabase.channel('custom-all-channel')

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
  })

// Export the channel for use in other parts of your application if needed
export { channel as supabaseChannel };
