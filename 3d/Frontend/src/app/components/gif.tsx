import Image from "next/image";

export default function Gif() {
    return(
        <div className="bg-neutral-900 flex items-center gap-1 px-10 py-10">
            {/* Text */}
            <div className="flex-1 text-white pl-10">
                <h2 className="text-4xl font-bold mb-4">
                    Experience the <span className="text-blue-400">Future</span>
                </h2>
                <p className="text-gray-300 mb-6">
                    Discover innovative solutions that transform how we work and create.
                </p>
                <button className="bg-blue-500 hover:bg-blue-600 text-white py-2 rounded">
                    Get Started
                </button>
            </div>

            {/* GIF */}
            <div className="flex-1 pr-10 pb-20 relative">
                <Image 
                    src="/gif1.gif" 
                    alt="demo"
                    width={900}
                    height={600}
                    unoptimized={true}
                    className="rounded-2xl"
                    style={{
                        maskImage: 'radial-gradient(ellipse, black 50%, transparent 100%)',
                        WebkitMaskImage: 'radial-gradient(ellipse, black 50%, transparent 100%)'
                    }}
                />
            </div>
        </div>
    )
}