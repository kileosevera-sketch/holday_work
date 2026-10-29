const Card = ({ icon, title, description }) => {
  return (
    <article className="flex items-center p-5 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer">
      {/* Sehemu ya Icon */}
      <div className="flex items-center justify-center w-12 h-12 bg-emerald-950/60 text-emerald-300 rounded-xl mr-4 shrink-0">
        <span className="text-2xl" aria-hidden="true">{icon}</span>
      </div>

      {/* Sehemu ya Maandishi */}
      <div>
        <h3 className="text-gray-900 font-semibold text-base mb-0.5">{title}</h3>
        <p className="text-gray-500 text-xs">{description}</p>
      </div>
    </article>
  );
};

export default Card;